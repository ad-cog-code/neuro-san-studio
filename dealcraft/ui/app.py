# =============================================================
# DealCraft — Flask Application
# File: ui/app.py
# Version: v0.1.0
# Description: Main Flask backend — handles routing, file
#              uploads, SSE progress streaming, and downloads
# =============================================================

import io
import json
import time
import os
from flask import (
    Flask, render_template, request,
    Response, jsonify, send_file
)
from werkzeug.utils import secure_filename
from neuro_san_client import DealCraftClient

# -------------------------------------------------------------
# App Configuration
# -------------------------------------------------------------
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = os.getenv('SECRET_KEY', 'dealcraft-dev-secret-change-in-prod')

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

# In-memory store for active runs and results
# In v1.0.0 this will be replaced with a database
runs    = {}
results = {}

# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------

def allowed_file(filename):
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def extract_text_from_file(file):
    """Extract plain text from an uploaded PDF, DOCX, or TXT file."""
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()

    if ext == 'pdf':
        import PyPDF2
        reader = PyPDF2.PdfReader(file)
        return '\n'.join(
            page.extract_text() or '' for page in reader.pages
        )

    elif ext == 'docx':
        import docx
        doc = docx.Document(file)
        return '\n'.join(para.text for para in doc.paragraphs)

    elif ext == 'txt':
        return file.read().decode('utf-8')

    return ''


def sse_event(payload: dict) -> str:
    """Format a dict as a Server-Sent Event string."""
    return f"data: {json.dumps(payload)}\n\n"


# -------------------------------------------------------------
# Routes
# -------------------------------------------------------------

@app.route('/')
def index():
    """Serve the main single-page UI."""
    return render_template('index.html')


@app.route('/run', methods=['POST'])
def run():
    """
    Accept form submission, extract RFP text from file if uploaded,
    create a run record, and return a run_id to the browser.
    """
    client_name = request.form.get('client_name', '').strip()
    rfp_text    = request.form.get('rfp_text', '').strip()

    # If a file was uploaded, extract its text (overrides textarea)
    uploaded = request.files.get('rfp_file')
    if uploaded and uploaded.filename and allowed_file(uploaded.filename):
        try:
            rfp_text = extract_text_from_file(uploaded)
        except Exception as e:
            return jsonify({'error': f'File extraction failed: {e}'}), 400

    if not client_name:
        return jsonify({'error': 'Client name is required.'}), 400

    run_id = str(int(time.time() * 1000))   # millisecond timestamp as ID
    runs[run_id] = {
        'client_name': client_name,
        'rfp_text':    rfp_text,
        'status':      'pending'
    }
    return jsonify({'run_id': run_id})


@app.route('/stream/<run_id>')
def stream(run_id):
    """
    SSE endpoint — runs the DealCraft agent pipeline and streams
    progress events back to the browser in real time.
    """
    run_data    = runs.get(run_id)
    if not run_data:
        return jsonify({'error': 'Run not found'}), 404

    client_name = run_data['client_name']
    rfp_text    = run_data['rfp_text']

    def generate():
        # Define the agent pipeline
        pipeline = [
            {
                'id':      'client-research-agent',
                'label':   'Client Research',
                'message': f'Researching {client_name}...'
            },
            {
                'id':      'rfp-analyzer-agent',
                'label':   'RFP Analysis',
                'message': 'Analyzing RFP document...'
            },
            {
                'id':      'competitive-intel-agent',
                'label':   'Competitive Intel',
                'message': 'Building competitive positioning...'
            },
            {
                'id':      'proposal-writer-agent',
                'label':   'Proposal Writing',
                'message': 'Drafting tailored proposal...'
            },
            {
                'id':      'report-assembler-agent',
                'label':   'Report Assembly',
                'message': 'Assembling final BD package...'
            },
        ]

        # Skip RFP analyzer if no RFP was provided
        if not rfp_text:
            pipeline = [
                a for a in pipeline
                if a['id'] != 'rfp-analyzer-agent'
            ]
            yield sse_event({
                'type':    'info',
                'message': 'No RFP provided — skipping RFP Analysis step.'
            })

        dc_client      = DealCraftClient()
        agent_outputs  = {}

        for agent in pipeline:
            agent_id = agent['id']

            # Notify browser: this agent is now running
            yield sse_event({
                'type':    'progress',
                'agent':   agent_id,
                'label':   agent['label'],
                'status':  'running',
                'message': agent['message']
            })

            try:
                output = dc_client.run_agent(
                    agent_id, client_name, rfp_text, agent_outputs
                )
                agent_outputs[agent_id] = output

                # Notify browser: this agent completed successfully
                yield sse_event({
                    'type':   'progress',
                    'agent':  agent_id,
                    'label':  agent['label'],
                    'status': 'done'
                })

            except Exception as e:
                yield sse_event({
                    'type':    'progress',
                    'agent':   agent_id,
                    'label':   agent['label'],
                    'status':  'error',
                    'message': str(e)
                })

        # Store final result — combine all agent outputs so the
        # leadership review agent has the full content to refine
        all_outputs = '\n\n'.join(agent_outputs.values())
        results[run_id] = all_outputs
        runs[run_id]['status'] = 'complete'

        yield sse_event({'type': 'complete', 'run_id': run_id})

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control':       'no-cache',
            'X-Accel-Buffering':   'no'     # Disable Nginx buffering if present
        }
    )


@app.route('/result/<run_id>')
def result(run_id):
    """Return the final BD Package output as JSON."""
    output = results.get(run_id)
    if output is None:
        return jsonify({'error': 'Result not ready or not found'}), 404
    return jsonify({'output': output})


@app.route('/refine', methods=['POST'])
def refine():
    """
    Accept leadership input (text or file), attach it to an existing
    run, and return the same run_id so the SSE stream can be reused.
    """
    run_id          = request.form.get('run_id', '').strip()
    leadership_text = request.form.get('leadership_text', '').strip()

    # File upload takes priority over pasted text
    uploaded = request.files.get('leadership_file')
    if uploaded and uploaded.filename and allowed_file(uploaded.filename):
        try:
            leadership_text = extract_text_from_file(uploaded)
        except Exception as e:
            return jsonify({'error': f'File extraction failed: {e}'}), 400

    if not run_id or run_id not in runs:
        return jsonify({'error': 'Invalid or expired run ID.'}), 400
    if not leadership_text:
        return jsonify({'error': 'Please provide leadership feedback.'}), 400

    # Increment revision counter
    runs[run_id]['revision']        = runs[run_id].get('revision', 0) + 1
    runs[run_id]['leadership_input'] = leadership_text
    runs[run_id]['status']           = 'pending'

    return jsonify({'run_id': run_id, 'revision': runs[run_id]['revision']})


@app.route('/stream-refine/<run_id>')
def stream_refine(run_id):
    """
    SSE endpoint for the leadership review refinement pass.
    Calls only the leadership-review-agent with the existing
    BD package and the new leadership input.
    """
    run_data = runs.get(run_id)
    if not run_data:
        return jsonify({'error': 'Run not found'}), 404

    leadership_input = run_data.get('leadership_input', '')
    existing_output  = results.get(run_id, '')
    revision         = run_data.get('revision', 1)
    client_name      = run_data.get('client_name', 'Client')

    def generate():
        yield sse_event({
            'type':    'progress',
            'agent':   'leadership-review-agent',
            'label':   'Leadership Review',
            'status':  'running',
            'message': f'Applying leadership feedback — Revision R{revision}...'
        })

        try:
            dc_client = DealCraftClient()
            refined   = dc_client.run_leadership_review(
                existing_output, leadership_input, revision, client_name
            )
            results[run_id]        = refined
            runs[run_id]['status'] = 'complete'

            yield sse_event({
                'type':   'progress',
                'agent':  'leadership-review-agent',
                'label':  'Leadership Review',
                'status': 'done'
            })
            yield sse_event({'type': 'complete', 'run_id': run_id, 'revision': revision})

        except Exception as e:
            yield sse_event({
                'type':    'progress',
                'agent':   'leadership-review-agent',
                'label':   'Leadership Review',
                'status':  'error',
                'message': str(e)
            })

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@app.route('/download/<run_id>')
def download(run_id):
    """Download the final BD Package as a .txt file."""
    output = results.get(run_id)
    if not output:
        return 'Result not found', 404

    run_data    = runs.get(run_id, {})
    client_slug = run_data.get('client_name', 'client').replace(' ', '-').lower()
    filename    = f'dealcraft-bd-package-{client_slug}-{run_id}.txt'

    buf = io.BytesIO(output.encode('utf-8'))
    buf.seek(0)

    return send_file(
        buf,
        as_attachment=True,
        download_name=filename,
        mimetype='text/plain'
    )


# -------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------

if __name__ == '__main__':
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)          # Only show errors, suppress request logs
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    port = int(os.getenv('PORT', 5171))
    print(f"Starting DealCraft on http://localhost:{port}")
    app.run(debug=False, port=port, threaded=True)