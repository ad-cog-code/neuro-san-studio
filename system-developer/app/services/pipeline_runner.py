import json
import logging
import time
from app.services.neuro_san_client import invoke_agent
from app.services.artifact_service import (
    save_artifact, save_session_meta, save_iteration_meta,
    parse_pipeline_response, ensure_session_dir
)
from app.services.board_service import build_board_state
from app.models.database import get_db

logger = logging.getLogger(__name__)

# Pipeline stages in execution order
PIPELINE_STAGES = [
    {"agent": "industry_sme", "label": "Industry SME", "icon": "bi-lightbulb", "desc": "Elaborating requirements"},
    {"agent": "business_analyst", "label": "Business Analyst", "icon": "bi-list-check", "desc": "Creating product backlog"},
    {"agent": "product_owner", "label": "Product Owner", "icon": "bi-bullseye", "desc": "Scoping MVP"},
    {"agent": "architect", "label": "Architect", "icon": "bi-diagram-3", "desc": "Designing system"},
    {"agent": "frontend_developer", "label": "Frontend Developer", "icon": "bi-palette", "desc": "Generating UI code"},
    {"agent": "backend_developer", "label": "Backend Developer", "icon": "bi-server", "desc": "Generating backend code"},
    {"agent": "execution_instructor", "label": "Execution Instructor", "icon": "bi-terminal", "desc": "Writing run instructions"},
    {"agent": "qa_tester", "label": "QA Tester", "icon": "bi-bug", "desc": "Testing & validation"},
    {"agent": "business_validator", "label": "Business Validator", "icon": "bi-shield-check", "desc": "Reviewing alignment"},
    {"agent": "technical_writer", "label": "Technical Writer", "icon": "bi-book", "desc": "Producing documentation"},
]


def get_stages():
    """Return the pipeline stage definitions for the UI."""
    return PIPELINE_STAGES


def run_pipeline(session_id, iteration, requirement, socketio, sid, feedback=None):
    """
    Execute the full SDLC pipeline via Neuro SAN.
    Emits SocketIO events for real-time progress tracking.
    """
    logger.info("Starting pipeline for session %s, iteration %d", session_id, iteration)

    # Save session and iteration metadata
    save_session_meta(session_id, requirement[:80])
    trigger = "feedback" if feedback else "initial"
    save_iteration_meta(session_id, iteration, trigger=trigger, feedback_text=feedback)

    # Prepare all stages as pending
    for stage in PIPELINE_STAGES:
        _update_stage_db(session_id, iteration, stage["agent"], "pending")

    # Emit initial state
    socketio.emit("pipeline_started", {
        "session_id": session_id,
        "iteration": iteration,
        "stages": PIPELINE_STAGES,
    }, room=sid)

    # Build the input for the agent
    if feedback:
        user_input = f"FEEDBACK ON PREVIOUS ITERATION:\n{feedback}\n\nORIGINAL REQUIREMENT:\n{requirement}"
    else:
        user_input = requirement

    sly_data = {
        "session_id": session_id,
        "iteration_count": iteration,
    }

    # Set all stages to "pending" in UI
    for stage in PIPELINE_STAGES:
        socketio.emit("stage_update", {
            "agent": stage["agent"],
            "status": "pending",
            "label": stage["label"],
            "desc": stage["desc"],
        }, room=sid)

    # Simulate stage-by-stage progress while calling the agent
    # Mark first stage as active
    socketio.emit("stage_update", {
        "agent": PIPELINE_STAGES[0]["agent"],
        "status": "active",
        "label": PIPELINE_STAGES[0]["label"],
        "desc": PIPELINE_STAGES[0]["desc"],
    }, room=sid)
    _update_stage_db(session_id, iteration, PIPELINE_STAGES[0]["agent"], "active")

    # Call Neuro SAN — single call, orchestrator handles delegation internally
    result = invoke_agent(user_input, sly_data=sly_data)

    if not result.get("ok"):
        # Pipeline failed — include error_code so the UI can show targeted guidance
        error_code = result.get("error_code", "unknown")
        error_msg  = result.get("msg", "Pipeline execution failed")
        logger.error("Pipeline failed [%s]: %s", error_code, error_msg)
        for stage in PIPELINE_STAGES:
            _update_stage_db(session_id, iteration, stage["agent"], "error")
        socketio.emit("pipeline_error", {
            "msg":        error_msg,
            "error_code": error_code,
            "session_id": session_id,
        }, room=sid)

        # Update iteration as failed
        conn = get_db()
        conn.execute(
            "UPDATE iterations SET completed_at = CURRENT_TIMESTAMP WHERE session_id = ? AND iteration_number = ?",
            (session_id, iteration)
        )
        conn.commit()
        conn.close()
        return

    # Parse the response into individual agent artifacts
    response_text = result.get("response", "")
    artifacts = parse_pipeline_response(response_text)

    # Process each artifact, update stages, and build board state progressively
    completed_agents = set()
    processed_artifacts = {}
    board_state = None

    for i, stage in enumerate(PIPELINE_STAGES):
        agent = stage["agent"]

        if agent in artifacts:
            # Save artifact to disk + DB
            save_artifact(session_id, iteration, agent, artifacts[agent])
            completed_agents.add(agent)
            processed_artifacts[agent] = artifacts[agent]

            # Mark this stage complete
            socketio.emit("stage_update", {
                "agent": agent,
                "status": "completed",
                "label": stage["label"],
                "desc": "Complete",
            }, room=sid)
            _update_stage_db(session_id, iteration, agent, "completed")

            # Compute and emit board state after each agent completes
            board_state = build_board_state(processed_artifacts)
            socketio.emit("board_update", {
                "board_state": board_state,
                "agent": agent,
            }, room=sid)

            # Mark next stage as active
            if i + 1 < len(PIPELINE_STAGES):
                next_stage = PIPELINE_STAGES[i + 1]
                socketio.emit("stage_update", {
                    "agent": next_stage["agent"],
                    "status": "active",
                    "label": next_stage["label"],
                    "desc": next_stage["desc"],
                }, room=sid)
                _update_stage_db(session_id, iteration, next_stage["agent"], "active")
        else:
            # Agent had no output — mark as skipped if not the full response fallback
            if "sdlc_orchestrator" not in artifacts:
                socketio.emit("stage_update", {
                    "agent": agent,
                    "status": "completed",
                    "label": stage["label"],
                    "desc": "Skipped (no markers)",
                }, room=sid)
                _update_stage_db(session_id, iteration, agent, "completed")

    # If we got the full response without markers, save it as a single artifact
    if "sdlc_orchestrator" in artifacts and len(artifacts) == 1:
        save_artifact_raw(session_id, iteration, response_text)
        for stage in PIPELINE_STAGES:
            socketio.emit("stage_update", {
                "agent": stage["agent"],
                "status": "completed",
                "label": stage["label"],
                "desc": "Complete",
            }, room=sid)
            _update_stage_db(session_id, iteration, stage["agent"], "completed")

    # Save final board state to database
    if board_state:
        try:
            conn = get_db()
            conn.execute(
                "INSERT OR REPLACE INTO board_states (session_id, iteration_number, board_json) VALUES (?, ?, ?)",
                (session_id, iteration, json.dumps(board_state))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Failed to save board state: %s", e)

    # Mark iteration as complete
    conn = get_db()
    conn.execute(
        "UPDATE iterations SET completed_at = CURRENT_TIMESTAMP WHERE session_id = ? AND iteration_number = ?",
        (session_id, iteration)
    )
    conn.commit()
    conn.close()

    # Emit pipeline completion
    run_instructions = artifacts.get("execution_instructor", "")
    socketio.emit("pipeline_complete", {
        "session_id": session_id,
        "iteration": iteration,
        "response": response_text[:500] + "..." if len(response_text) > 500 else response_text,
        "artifacts_count": len(completed_agents),
        "run_instructions": run_instructions,
        "has_artifacts": len(completed_agents) > 0,
        "board_state": board_state,
    }, room=sid)

    logger.info("Pipeline complete for session %s: %d artifacts saved", session_id, len(completed_agents))


def save_artifact_raw(session_id, iteration, content):
    """Save the full pipeline response when stage markers are not present."""
    import os
    from app.services.artifact_service import ensure_session_dir

    iter_dir = ensure_session_dir(session_id, iteration)
    file_path = os.path.join(iter_dir, "full_pipeline_output.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    conn = get_db()
    conn.execute(
        """INSERT INTO artifacts (session_id, iteration_number, artifact_type, agent_name, file_path)
           VALUES (?, ?, ?, ?, ?)""",
        (session_id, iteration, "full_output", "sdlc_orchestrator", file_path)
    )
    conn.commit()
    conn.close()


def _update_stage_db(session_id, iteration, agent_name, status):
    """Update pipeline stage status in the database."""
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM pipeline_stages WHERE session_id = ? AND iteration_number = ? AND agent_name = ?",
        (session_id, iteration, agent_name)
    ).fetchone()

    if existing:
        if status == "active":
            conn.execute(
                "UPDATE pipeline_stages SET status = ?, started_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, existing["id"])
            )
        elif status in ("completed", "error"):
            conn.execute(
                "UPDATE pipeline_stages SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, existing["id"])
            )
        else:
            conn.execute(
                "UPDATE pipeline_stages SET status = ? WHERE id = ?",
                (status, existing["id"])
            )
    else:
        conn.execute(
            "INSERT INTO pipeline_stages (session_id, iteration_number, agent_name, status) VALUES (?, ?, ?, ?)",
            (session_id, iteration, agent_name, status)
        )

    conn.commit()
    conn.close()
