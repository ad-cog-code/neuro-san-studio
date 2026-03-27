/* =============================================================
   DealCraft — Frontend Logic
   File: ui/static/js/dealcraft.js
   Version: v0.1.0
   Handles: form submission, SSE progress, output display,
            file upload UX, download
   ============================================================= */

'use strict';

// ── State ───────────────────────────────────────────────────
const state = {
  runId:       null,
  clientName:  '',
  agentsDone:  0,
  agentTotal:  5,
  evtSource:   null
};

// ── DOM Refs ─────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const sections = {
  input:    $('section-input'),
  progress: $('section-progress'),
  output:   $('section-output')
};

const form         = $('dealcraft-form');
const btnSubmit    = $('btn-submit');
const errorMsg     = $('error-msg');
const uploadArea   = $('upload-area');
const uploadFile   = $('rfp_file');
const uploadLabel  = $('upload-filename');
const progressBar  = $('progress-bar');
const progressText = $('progress-status-text');
const outputPre    = $('output-content');
const btnDownload  = $('btn-download');
const btnNew       = $('btn-new');

// ── Helpers ──────────────────────────────────────────────────

function show(section) {
  Object.values(sections).forEach(s => s.classList.add('hidden'));
  sections[section].classList.remove('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function setError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.toggle('visible', !!msg);
}

function setProgress(pct, msg) {
  progressBar.style.width = `${pct}%`;
  if (msg) progressText.textContent = msg;
}

function agentEl(agentId) {
  return $(`agent-${agentId}`);
}

function setAgentState(agentId, status, msg) {
  const el = agentEl(agentId);
  if (!el) return;
  el.className = `agent-card ${status}`;
  el.querySelector('.agent-status').textContent = msg || status;
}

function resetAgents() {
  const agents = [
    'client-research-agent',
    'rfp-analyzer-agent',
    'competitive-intel-agent',
    'proposal-writer-agent',
    'report-assembler-agent'
  ];
  agents.forEach(id => setAgentState(id, '', 'Waiting'));
}

// ── File Upload UX ────────────────────────────────────────────

uploadFile.addEventListener('change', () => {
  const f = uploadFile.files[0];
  uploadLabel.textContent = f ? `✓ ${f.name}` : '';
});

['dragover', 'dragleave', 'drop'].forEach(evt => {
  uploadArea.addEventListener(evt, e => {
    e.preventDefault();
    if (evt === 'dragover') uploadArea.classList.add('drag-over');
    if (evt === 'dragleave' || evt === 'drop') {
      uploadArea.classList.remove('drag-over');
    }
    if (evt === 'drop' && e.dataTransfer.files.length) {
      uploadFile.files = e.dataTransfer.files;
      uploadLabel.textContent = `✓ ${uploadFile.files[0].name}`;
    }
  });
});

// ── Form Submission ───────────────────────────────────────────

form.addEventListener('submit', async e => {
  e.preventDefault();
  setError('');

  const clientName = $('client_name').value.trim();
  if (!clientName) { setError('Please enter a client name.'); return; }

  btnSubmit.disabled = true;
  btnSubmit.textContent = 'Starting...';

  const fd = new FormData(form);
  let runId;

  try {
    const res  = await fetch('/run', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.error) { throw new Error(data.error); }
    runId = data.run_id;
  } catch (err) {
    setError(err.message || 'Failed to start run. Please try again.');
    btnSubmit.disabled = false;
    btnSubmit.innerHTML = '<span class="btn-icon">⚡</span> Generate BD Package';
    return;
  }

  state.runId      = runId;
  state.clientName = clientName;
  state.agentsDone = 0;

  $('progress-client-name').textContent = clientName;
  $('output-client-name').textContent   = clientName;

  resetAgents();
  setProgress(0, 'Initializing DealCraft agents...');
  show('progress');

  startSSE(runId);
});

// ── SSE Progress Stream ───────────────────────────────────────

function startSSE(runId) {
  if (state.evtSource) state.evtSource.close();

  const es = new EventSource(`/stream/${runId}`);
  state.evtSource = es;

  es.onmessage = e => {
    let payload;
    try { payload = JSON.parse(e.data); } catch { return; }

    switch (payload.type) {

      case 'info':
        // Informational messages (e.g., skipped agent)
        if (payload.message?.includes('rfp-analyzer')) {
          setAgentState('rfp-analyzer-agent', 'skipped', 'Skipped — no RFP provided');
          state.agentTotal = 4;
        }
        break;

      case 'progress':
        handleProgress(payload);
        break;

      case 'complete':
        es.close();
        fetchResult(runId);
        break;
    }
  };

  es.onerror = () => {
    es.close();
    setProgress(100, 'Connection error — attempting to fetch result...');
    setTimeout(() => fetchResult(runId), 2000);
  };
}

function handleProgress(p) {
  const { agent, status, message, label } = p;

  if (status === 'running') {
    setAgentState(agent, 'running', message || 'Running...');
    const pct = Math.round((state.agentsDone / state.agentTotal) * 90);
    setProgress(pct, `${label}: ${message || 'Processing...'}`);
  }

  if (status === 'done') {
    setAgentState(agent, 'done', 'Complete ✓');
    state.agentsDone++;
    const pct = Math.round((state.agentsDone / state.agentTotal) * 90);
    setProgress(pct, `${label} complete.`);
  }

  if (status === 'error') {
    setAgentState(agent, 'error', `Error: ${message || 'Failed'}`);
  }
}

// ── Fetch & Display Result ────────────────────────────────────

async function fetchResult(runId) {
  setProgress(95, 'Assembling BD package...');

  try {
    const res  = await fetch(`/result/${runId}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    setProgress(100, 'BD package ready!');

    outputPre.textContent = data.output;

    // Brief pause so user sees 100% before switching screen
    setTimeout(() => show('output'), 600);

  } catch (err) {
    progressText.textContent = `Error: ${err.message}`;
  }
}

// ── Download ──────────────────────────────────────────────────

btnDownload.addEventListener('click', () => {
  if (state.runId) {
    window.location.href = `/download/${state.runId}`;
  }
});

// ── Leadership Review State ───────────────────────────────────
const leadershipState = {
  revisions:   [],   // [{revision, input, output}]
  currentRev:  0
};

// ── Leadership DOM Refs ───────────────────────────────────────
const leadershipCard    = $('leadership-card');
const leadershipFile    = $('leadership_file');
const leadershipLabel   = $('leadership-upload-filename');
const leadershipText    = $('leadership_text');
const leadershipError   = $('leadership-error-msg');
const revisionBadge     = $('revision-badge');
const revisionHistory   = $('revision-history');
const btnRefine         = $('btn-refine');

// ── Leadership File Upload UX ─────────────────────────────────
leadershipFile.addEventListener('change', () => {
  const f = leadershipFile.files[0];
  leadershipLabel.textContent = f ? `✓ ${f.name}` : '';
});

const leadershipUploadArea = $('leadership-upload-area');
['dragover','dragleave','drop'].forEach(evt => {
  leadershipUploadArea.addEventListener(evt, e => {
    e.preventDefault();
    if (evt === 'dragover') leadershipUploadArea.classList.add('drag-over');
    if (evt === 'dragleave' || evt === 'drop') leadershipUploadArea.classList.remove('drag-over');
    if (evt === 'drop' && e.dataTransfer.files.length) {
      leadershipFile.files = e.dataTransfer.files;
      leadershipLabel.textContent = `✓ ${leadershipFile.files[0].name}`;
    }
  });
});

// ── Refine / Leadership Review Submission ─────────────────────
btnRefine.addEventListener('click', async () => {
  leadershipError.classList.remove('visible');

  const feedbackText = leadershipText.value.trim();
  const feedbackFile = leadershipFile.files[0];

  if (!feedbackText && !feedbackFile) {
    leadershipError.textContent = 'Please enter feedback or upload a document.';
    leadershipError.classList.add('visible');
    return;
  }

  btnRefine.disabled = true;
  btnRefine.textContent = 'Refining...';
  leadershipCard.classList.add('refining');

  // Submit to /refine
  const fd = new FormData();
  fd.append('run_id', state.runId);
  fd.append('leadership_text', feedbackText);
  if (feedbackFile) fd.append('leadership_file', feedbackFile);

  let revision;
  try {
    const res  = await fetch('/refine', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    revision = data.revision;
  } catch (err) {
    leadershipError.textContent = err.message || 'Failed to submit feedback.';
    leadershipError.classList.add('visible');
    btnRefine.disabled = false;
    btnRefine.innerHTML = '<span class="btn-icon">🔄</span> Regenerate BD Package';
    leadershipCard.classList.remove('refining');
    return;
  }

  // Show single-agent progress inline in output area
  outputPre.textContent = `⏳ Applying leadership feedback — Revision R${revision}...\n\nPlease wait...`;

  // Store current input for history
  const inputSummary = feedbackText.substring(0, 80) + (feedbackText.length > 80 ? '...' : '');

  // Start SSE for refinement
  startRefineSSE(state.runId, revision, inputSummary);
});

function startRefineSSE(runId, revision, inputSummary) {
  if (state.evtSource) state.evtSource.close();

  const es = new EventSource(`/stream-refine/${runId}`);
  state.evtSource = es;

  es.onmessage = e => {
    let payload;
    try { payload = JSON.parse(e.data); } catch { return; }

    if (payload.type === 'progress' && payload.status === 'done') {
      outputPre.textContent = '✅ Revision complete — fetching updated package...';
    }

    if (payload.type === 'complete') {
      es.close();
      fetchRefinedResult(runId, revision, inputSummary);
    }
  };

  es.onerror = () => {
    es.close();
    setTimeout(() => fetchRefinedResult(runId, revision, inputSummary), 2000);
  };
}

async function fetchRefinedResult(runId, revision, inputSummary) {
  try {
    const res  = await fetch(`/result/${runId}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    // Update output
    outputPre.textContent = data.output;

    // Update revision badge
    revisionBadge.textContent = `Revision R${revision}`;

    // Add to revision history
    leadershipState.revisions.push({ revision, inputSummary, output: data.output });
    leadershipState.currentRev = revision;
    renderRevisionHistory();

    // Clear inputs
    leadershipText.value = '';
    leadershipFile.value = '';
    leadershipLabel.textContent = '';

  } catch (err) {
    leadershipError.textContent = `Error: ${err.message}`;
    leadershipError.classList.add('visible');
  } finally {
    btnRefine.disabled = false;
    btnRefine.innerHTML = '<span class="btn-icon">🔄</span> Regenerate BD Package';
    leadershipCard.classList.remove('refining');
  }
}

function renderRevisionHistory() {
  revisionHistory.innerHTML = '';
  if (leadershipState.revisions.length === 0) return;

  // Label
  const label = document.createElement('p');
  label.style.cssText = 'font-size:0.78rem;color:var(--text-dim);margin-bottom:0.4rem;';
  label.textContent = 'Previous revisions (click to view):';
  revisionHistory.appendChild(label);

  // Pill for original
  const origPill = document.createElement('span');
  origPill.className = 'revision-pill' + (leadershipState.currentRev === 0 ? ' active' : '');
  origPill.textContent = 'Draft v0.1 (Original)';
  origPill.onclick = () => {
    // Restore original — re-fetch would be needed; for now just inform
    leadershipState.currentRev = 0;
    renderRevisionHistory();
    outputPre.textContent = leadershipState.revisions[0]?.output || '(Original output no longer cached)';
    revisionBadge.textContent = 'Draft v0.1';
  };
  revisionHistory.appendChild(origPill);

  leadershipState.revisions.forEach(rev => {
    const pill = document.createElement('span');
    pill.className = 'revision-pill' + (leadershipState.currentRev === rev.revision ? ' active' : '');
    pill.title = rev.inputSummary;
    pill.textContent = `R${rev.revision}`;
    pill.onclick = () => {
      outputPre.textContent = rev.output;
      revisionBadge.textContent = `Revision R${rev.revision}`;
      leadershipState.currentRev = rev.revision;
      renderRevisionHistory();
    };
    revisionHistory.appendChild(pill);
  });
}

// ── New Opportunity (Start Over) ──────────────────────────────

btnNew.addEventListener('click', () => {
  // Reset all form and state
  form.reset();
  uploadLabel.textContent = '';
  errorMsg.classList.remove('visible');
  btnSubmit.disabled = false;
  btnSubmit.innerHTML = '<span class="btn-icon">⚡</span> Generate BD Package';

  // Reset leadership panel
  leadershipText.value     = '';
  leadershipFile.value     = '';
  leadershipLabel.textContent     = '';
  leadershipError.classList.remove('visible');
  leadershipCard.classList.remove('refining');
  revisionBadge.textContent = 'Draft v0.1';
  revisionHistory.innerHTML = '';
  btnRefine.disabled = false;
  btnRefine.innerHTML = '<span class="btn-icon">🔄</span> Regenerate BD Package';

  // Reset state
  state.runId      = null;
  state.agentsDone = 0;
  state.agentTotal = 5;
  leadershipState.revisions   = [];
  leadershipState.currentRev  = 0;

  if (state.evtSource) state.evtSource.close();
  show('input');
});