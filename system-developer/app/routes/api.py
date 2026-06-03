from flask import Blueprint, request, jsonify, send_file
from app.services.session_service import (
    create_session, get_session, list_sessions,
    update_session_status, create_iteration, get_session_requirement
)
from app.services.artifact_service import (
    get_artifacts, get_artifact_content, save_feedback
)
from app.services.zip_service import create_session_zip, create_iteration_zip

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/build", methods=["POST"])
def build():
    try:
        data = request.get_json()
        requirement = data.get("requirement", "").strip()
        if not requirement:
            return jsonify({"ok": False, "msg": "Requirement cannot be empty"})

        session = create_session(requirement)
        return jsonify({
            "ok": True,
            "session_id": session["id"],
            "iteration": session["iteration"],
            "msg": "Session created, starting pipeline..."
        })
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@api_bp.route("/sessions")
def sessions_list():
    try:
        sessions = list_sessions()
        return jsonify({"ok": True, "data": sessions})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@api_bp.route("/session/<session_id>")
def session_detail(session_id):
    try:
        session = get_session(session_id)
        if not session:
            return jsonify({"ok": False, "msg": "Session not found"})
        return jsonify({"ok": True, "data": session})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@api_bp.route("/session/<session_id>/artifacts")
def session_artifacts(session_id):
    try:
        iteration = request.args.get("iteration", type=int)
        artifacts = get_artifacts(session_id, iteration)
        return jsonify({"ok": True, "data": artifacts})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@api_bp.route("/session/<session_id>/artifact/<int:artifact_id>")
def artifact_detail(session_id, artifact_id):
    try:
        artifact = get_artifact_content(session_id, artifact_id)
        if not artifact:
            return jsonify({"ok": False, "msg": "Artifact not found"})
        return jsonify({"ok": True, "data": artifact})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@api_bp.route("/session/<session_id>/board")
def session_board(session_id):
    try:
        session = get_session(session_id)
        if not session:
            return jsonify({"ok": False, "msg": "Session not found"})
        return jsonify({"ok": True, "data": session.get("board_state")})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@api_bp.route("/session/<session_id>/feedback", methods=["POST"])
def submit_feedback(session_id):
    try:
        data = request.get_json()
        feedback_text = data.get("feedback", "").strip()
        if not feedback_text:
            return jsonify({"ok": False, "msg": "Feedback cannot be empty"})

        session = get_session(session_id)
        if not session:
            return jsonify({"ok": False, "msg": "Session not found"})

        current_iter = session["iteration_count"]
        save_feedback(session_id, current_iter, feedback_text)
        new_iter = create_iteration(session_id, trigger="feedback", feedback_text=feedback_text)

        return jsonify({
            "ok": True,
            "iteration": new_iter,
            "msg": f"Feedback received. Starting iteration {new_iter}..."
        })
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@api_bp.route("/session/<session_id>/ship", methods=["POST"])
def ship_session(session_id):
    try:
        update_session_status(session_id, "completed")
        return jsonify({"ok": True, "msg": "Session marked as completed!"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@api_bp.route("/session/<session_id>/abandon", methods=["POST"])
def abandon_session(session_id):
    try:
        update_session_status(session_id, "abandoned")
        return jsonify({"ok": True, "msg": "Session abandoned. Artifacts preserved."})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@api_bp.route("/session/<session_id>/download")
def download_session(session_id):
    try:
        zip_buffer = create_session_zip(session_id)
        if not zip_buffer:
            return jsonify({"ok": False, "msg": "Session directory not found"})

        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"session_{session_id}.zip"
        )
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@api_bp.route("/session/<session_id>/download/<int:iteration>")
def download_iteration(session_id, iteration):
    try:
        zip_buffer = create_iteration_zip(session_id, iteration)
        if not zip_buffer:
            return jsonify({"ok": False, "msg": "Iteration directory not found"})

        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"session_{session_id}_iter_{iteration}.zip"
        )
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})
