import os
import sys
import logging

# Ensure the system-developer directory is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_socketio import SocketIO, emit
from app.config import PORT, SECRET_KEY
from app.models.database import init_db
from app.routes.main import main_bp
from app.routes.api import api_bp
from app.services.pipeline_runner import run_pipeline, get_stages
from app.services.session_service import (
    get_session, get_session_requirement, create_iteration
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=360, ping_interval=25)

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(api_bp)


# --- SocketIO Events ---

@socketio.on("connect")
def on_connect():
    logger.info("Client connected")
    emit("status", {"msg": "Connected to System Developer"})


@socketio.on("start_pipeline")
def handle_start_pipeline(data):
    """User clicked 'Build It'. Run the full SDLC pipeline."""
    requirement = data.get("requirement", "").strip()
    session_id = data.get("session_id", "")
    iteration = data.get("iteration", 1)

    if not requirement or not session_id:
        emit("pipeline_error", {"msg": "Missing requirement or session ID"})
        return

    logger.info("Starting pipeline: session=%s, iter=%d", session_id, iteration)

    # Run pipeline in background thread so we don't block SocketIO
    from flask import request as flask_request
    sid = flask_request.sid
    socketio.start_background_task(
        run_pipeline, session_id, iteration, requirement, socketio, sid
    )


@socketio.on("submit_feedback")
def handle_feedback(data):
    """User submitted feedback. Create new iteration and re-run pipeline."""
    session_id = data.get("session_id", "")
    feedback = data.get("feedback", "").strip()

    if not session_id or not feedback:
        emit("pipeline_error", {"msg": "Missing session ID or feedback"})
        return

    # Get original requirement
    requirement = get_session_requirement(session_id)
    if not requirement:
        emit("pipeline_error", {"msg": "Session not found"})
        return

    # Create new iteration
    new_iter = create_iteration(session_id, trigger="feedback", feedback_text=feedback)

    logger.info("Feedback received: session=%s, iter=%d", session_id, new_iter)

    from flask import request as flask_request
    sid = flask_request.sid
    socketio.start_background_task(
        run_pipeline, session_id, new_iter, requirement, socketio, sid, feedback=feedback
    )


@socketio.on("disconnect")
def on_disconnect():
    logger.info("Client disconnected")


# --- Main ---

if __name__ == "__main__":
    init_db()
    logger.info("Database initialized")
    port = int(os.getenv("PORT", PORT))
    print(f"\n  System Developer SDLC Pipeline")
    print(f"  http://localhost:{port}")
    print(f"  Press Ctrl+C to stop\n")
    socketio.run(app, debug=True, host="0.0.0.0", port=port, use_reloader=False)
