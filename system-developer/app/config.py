import os
from dotenv import load_dotenv

# Load .env from project root (system-developer/)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_project_root, ".env"))

PORT = int(os.getenv("PORT", 5003))
SECRET_KEY = os.getenv("SECRET_KEY", "system-developer-dev-secret")
NEURO_SAN_HOST = os.getenv("NEURO_SAN_SERVER_HOST", "localhost")
NEURO_SAN_PORT = int(os.getenv("NEURO_SAN_SERVER_HTTP_PORT", 8080))
AGENT_NETWORK = os.getenv("AGENT_NETWORK", "sdlc_pipeline")

ARTIFACT_STORE = os.path.join(_project_root, "artifact_store")
SESSIONS_DIR = os.path.join(ARTIFACT_STORE, "sessions")

# Ensure directories exist
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(os.path.join(ARTIFACT_STORE, "db"), exist_ok=True)
