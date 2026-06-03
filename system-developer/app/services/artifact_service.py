import os
import re
import json
import logging
from datetime import datetime
from app.config import SESSIONS_DIR
from app.models.database import get_db

logger = logging.getLogger(__name__)

# Maps agent names to artifact types and file extensions
ARTIFACT_MAP = {
    "industry_sme": {"type": "requirements_document", "ext": ".md"},
    "business_analyst": {"type": "product_backlog", "ext": ".json"},
    "product_owner": {"type": "mvp_plan", "ext": ".json"},
    "architect": {"type": "architecture_document", "ext": ".md"},
    "frontend_developer": {"type": "frontend_code", "ext": ".md"},
    "backend_developer": {"type": "backend_code", "ext": ".md"},
    "execution_instructor": {"type": "run_instructions", "ext": ".md"},
    "qa_tester": {"type": "test_results", "ext": ".json"},
    "business_validator": {"type": "validation_report", "ext": ".md"},
    "technical_writer": {"type": "documentation_package", "ext": ".md"},
}


def get_session_dir(session_id):
    return os.path.join(SESSIONS_DIR, f"session_{session_id}")


def get_iteration_dir(session_id, iteration):
    return os.path.join(get_session_dir(session_id), f"iteration_{iteration}")


def ensure_session_dir(session_id, iteration=1):
    """Create the session and iteration directory structure."""
    iter_dir = get_iteration_dir(session_id, iteration)
    os.makedirs(iter_dir, exist_ok=True)
    os.makedirs(os.path.join(iter_dir, "code", "frontend"), exist_ok=True)
    os.makedirs(os.path.join(iter_dir, "code", "backend"), exist_ok=True)
    os.makedirs(os.path.join(iter_dir, "documentation"), exist_ok=True)
    return iter_dir


def save_artifact(session_id, iteration, agent_name, content):
    """Save an artifact to disk and record in database."""
    if agent_name not in ARTIFACT_MAP:
        logger.warning("Unknown agent name: %s", agent_name)
        return None

    info = ARTIFACT_MAP[agent_name]
    iter_dir = ensure_session_dir(session_id, iteration)

    # Determine file path
    if agent_name == "frontend_developer":
        file_path = os.path.join(iter_dir, "code", f"frontend_code{info['ext']}")
        # Also extract individual files from the code output
        _extract_code_files(content, os.path.join(iter_dir, "code", "frontend"))
    elif agent_name == "backend_developer":
        file_path = os.path.join(iter_dir, "code", f"backend_code{info['ext']}")
        _extract_code_files(content, os.path.join(iter_dir, "code", "backend"))
    elif agent_name == "technical_writer":
        file_path = os.path.join(iter_dir, "documentation", f"documentation_package{info['ext']}")
        _extract_doc_files(content, os.path.join(iter_dir, "documentation"))
    else:
        file_path = os.path.join(iter_dir, f"{info['type']}{info['ext']}")

    # Write content to file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Saved artifact: %s", file_path)
    except Exception as e:
        logger.error("Error saving artifact %s: %s", file_path, e)
        return None

    # Record in database
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO artifacts (session_id, iteration_number, artifact_type, agent_name, file_path)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, iteration, info["type"], agent_name, file_path)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("Error recording artifact in DB: %s", e)

    return file_path


def _extract_code_files(content, base_dir):
    """Extract individual code files from ### FILE: path markers."""
    pattern = r"###\s*FILE:\s*(.+?)\n```\w*\n(.*?)```"
    matches = re.findall(pattern, content, re.DOTALL)
    for file_path, file_content in matches:
        file_path = file_path.strip()
        full_path = os.path.join(base_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file_content.strip())
            logger.info("Extracted code file: %s", full_path)
        except Exception as e:
            logger.error("Error extracting file %s: %s", full_path, e)


def _extract_doc_files(content, base_dir):
    """Extract documentation files from ### FILE: path markers."""
    _extract_code_files(content, base_dir)


def get_artifacts(session_id, iteration=None):
    """Get all artifacts for a session, optionally filtered by iteration."""
    conn = get_db()
    if iteration:
        rows = conn.execute(
            "SELECT * FROM artifacts WHERE session_id = ? AND iteration_number = ? ORDER BY created_at",
            (session_id, iteration)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM artifacts WHERE session_id = ? ORDER BY iteration_number, created_at",
            (session_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_artifact_content(session_id, artifact_id):
    """Read an artifact's content from disk."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM artifacts WHERE id = ? AND session_id = ?",
        (artifact_id, session_id)
    ).fetchone()
    conn.close()

    if not row:
        return None

    artifact = dict(row)
    try:
        with open(artifact["file_path"], "r", encoding="utf-8") as f:
            artifact["content"] = f.read()
    except FileNotFoundError:
        artifact["content"] = "[File not found on disk]"
    except Exception as e:
        artifact["content"] = f"[Error reading file: {e}]"

    return artifact


def save_session_meta(session_id, name, status="active"):
    """Save session metadata JSON to the session directory."""
    session_dir = get_session_dir(session_id)
    os.makedirs(session_dir, exist_ok=True)
    meta = {
        "id": session_id,
        "name": name,
        "status": status,
        "created_at": datetime.utcnow().isoformat(),
    }
    meta_path = os.path.join(session_dir, "session_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    return meta_path


def save_iteration_meta(session_id, iteration, trigger="initial", feedback_text=None):
    """Save iteration metadata JSON."""
    iter_dir = ensure_session_dir(session_id, iteration)
    meta = {
        "iteration": iteration,
        "trigger": trigger,
        "feedback_text": feedback_text,
        "timestamp": datetime.utcnow().isoformat(),
        "stages_executed": [],
    }
    meta_path = os.path.join(iter_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    return meta_path


def save_feedback(session_id, iteration, feedback_text):
    """Append feedback to the session's feedback log."""
    session_dir = get_session_dir(session_id)
    log_path = os.path.join(session_dir, "feedback_log.json")

    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            log = json.load(f)
    else:
        log = []

    log.append({
        "iteration": iteration,
        "timestamp": datetime.utcnow().isoformat(),
        "feedback_text": feedback_text,
    })

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

    return log_path


def parse_pipeline_response(response_text):
    """
    Parse the orchestrator's response to extract individual agent outputs.
    Looks for [STAGE:agent_name:START] ... [STAGE:agent_name:COMPLETE] markers.
    Returns a dict of {agent_name: content}.
    """
    artifacts = {}
    pattern = r"\[STAGE:(\w+):START\]\s*(.*?)\s*\[STAGE:\1:COMPLETE\]"
    matches = re.findall(pattern, response_text, re.DOTALL)

    for agent_name, content in matches:
        artifacts[agent_name] = content.strip()
        logger.info("Parsed artifact from agent: %s (%d chars)", agent_name, len(content))

    # If no stage markers found, try to split by section headers as fallback
    if not artifacts:
        logger.warning("No stage markers found in response, using full response as single artifact")
        artifacts["sdlc_orchestrator"] = response_text

    return artifacts
