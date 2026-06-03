import os
import io
import zipfile
import logging
from app.services.artifact_service import get_session_dir

logger = logging.getLogger(__name__)


def create_session_zip(session_id):
    """
    Create a ZIP archive of the entire session directory.
    Returns a BytesIO object containing the ZIP data.
    """
    session_dir = get_session_dir(session_id)

    if not os.path.exists(session_dir):
        logger.error("Session directory not found: %s", session_dir)
        return None

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(session_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, os.path.dirname(session_dir))
                zf.write(file_path, arc_name)

    zip_buffer.seek(0)
    logger.info("Created ZIP for session %s", session_id)
    return zip_buffer


def create_iteration_zip(session_id, iteration):
    """
    Create a ZIP archive of a specific iteration directory.
    Returns a BytesIO object containing the ZIP data.
    """
    from app.services.artifact_service import get_iteration_dir
    iter_dir = get_iteration_dir(session_id, iteration)

    if not os.path.exists(iter_dir):
        logger.error("Iteration directory not found: %s", iter_dir)
        return None

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(iter_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, os.path.dirname(iter_dir))
                zf.write(file_path, arc_name)

    zip_buffer.seek(0)
    return zip_buffer
