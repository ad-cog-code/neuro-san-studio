from flask import Blueprint, render_template, redirect, url_for
from app.services.session_service import get_session, list_sessions
from app.services.artifact_service import get_artifacts
from app.services.pipeline_runner import get_stages

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    sessions = list_sessions()
    return render_template("home.html", sessions=sessions)


@main_bp.route("/session/<session_id>")
def dashboard(session_id):
    session = get_session(session_id)
    if not session:
        return redirect(url_for("main.home"))

    artifacts = get_artifacts(session_id, session["iteration_count"])
    stages = get_stages()

    return render_template(
        "dashboard.html",
        session=session,
        artifacts=artifacts,
        stages=stages,
    )


@main_bp.route("/sessions")
def session_history():
    sessions = list_sessions()
    return render_template("session_history.html", sessions=sessions)
