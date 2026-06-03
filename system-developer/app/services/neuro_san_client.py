import json
import logging
import requests
from app.config import NEURO_SAN_HOST, NEURO_SAN_PORT, AGENT_NETWORK

logger = logging.getLogger(__name__)

BASE_URL = f"http://{NEURO_SAN_HOST}:{NEURO_SAN_PORT}"

# ── Error pattern detection ────────────────────────────────────────────────────
# Strings that appear in the response TEXT when Neuro SAN / the LLM hits a limit.
# Each entry is (substring_to_match, error_code, user_facing_message).
_RESPONSE_ERROR_PATTERNS = [
    # Neuro SAN server-busy / concurrency guard (openai.BadRequestError)
    ("Patience, please",        "server_busy",    "Neuro SAN server is busy processing another request. Please wait and retry."),
    ("I'm working on it",       "server_busy",    "Neuro SAN server is busy processing another request. Please wait and retry."),
    # LLM context-window / token errors that bubble up into the response text
    ("context_length_exceeded", "token_limit",    "The request exceeded the model's context window. Try a shorter input or split the task."),
    ("context window",          "token_limit",    "The request exceeded the model's context window. Try a shorter input or split the task."),
    ("maximum context length",  "token_limit",    "The request exceeded the model's context window. Try a shorter input or split the task."),
    ("max_tokens",              "token_limit",    "The model reached its maximum token output. The response may be incomplete."),
    ("token limit",             "token_limit",    "The model reached its token limit. Try a shorter input or split the task."),
    # Rate limiting
    ("rate limit",              "rate_limit",     "The LLM API rate limit was hit. Wait a minute and retry."),
    ("rate_limit",              "rate_limit",     "The LLM API rate limit was hit. Wait a minute and retry."),
    ("429",                     "rate_limit",     "The LLM API rate limit was hit. Wait a minute and retry."),
    # Overloaded / unavailable
    ("overloaded",              "api_overloaded", "The LLM API is overloaded. Wait a few minutes and retry."),
    ("service unavailable",     "api_overloaded", "The LLM API is temporarily unavailable. Wait a few minutes and retry."),
]


def _classify_response_text(text):
    """
    Check response text for known error patterns.

    Returns (error_code, user_msg) if an error is detected, else (None, None).
    """
    if not text:
        return None, None
    lower = text.lower()
    for pattern, code, msg in _RESPONSE_ERROR_PATTERNS:
        if pattern.lower() in lower:
            return code, msg
    return None, None


def invoke_agent(user_input, sly_data=None):
    """
    Invoke the SDLC pipeline agent network via Neuro SAN HTTP API.

    Endpoint: POST /api/v1/{network}/streaming_chat
    Payload:  {"user_message": {"type": "HUMAN", "text": "..."}}
    Response: JSON-lines (one JSON object per line)

    Returns dict with keys:
        ok         (bool)   — True on success
        response   (str)    — Agent text (only when ok=True)
        sly_data   (dict)   — Returned sly_data (only when ok=True)
        msg        (str)    — Error description (only when ok=False)
        error_code (str)    — Machine-readable code (only when ok=False):
                              "token_limit" | "server_busy" | "rate_limit" |
                              "api_overloaded" | "empty_response" |
                              "connection" | "timeout" | "http_error" | "unknown"
    """
    url = f"{BASE_URL}/api/v1/{AGENT_NETWORK}/streaming_chat"
    payload = {
        "user_message": {
            "type": "HUMAN",
            "text": user_input,
        }
    }
    if sly_data:
        payload["sly_data"] = sly_data

    try:
        logger.info("Invoking agent network '%s' at %s", AGENT_NETWORK, url)
        logger.info("Input: %s...", user_input[:200])

        resp = requests.post(url, json=payload, stream=True, timeout=600)
        resp.raise_for_status()

        # Parse streaming JSON-lines response — extract final answer
        last_text = ""
        last_sly_data = {}

        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.strip():
                continue
            try:
                result = json.loads(line)

                # ── Top-level error field (some Neuro SAN versions) ──
                if "error" in result:
                    err_msg = str(result["error"])
                    logger.error("Neuro SAN returned top-level error: %s", err_msg)
                    code, friendly = _classify_response_text(err_msg)
                    return {
                        "ok": False,
                        "error_code": code or "unknown",
                        "msg": friendly or f"Neuro SAN error: {err_msg}",
                    }

                # ── Normal response path ──
                # Structure: response.chat_context.chat_histories[-1].messages[-1].text
                resp_obj = result.get("response", {})

                if "sly_data" in resp_obj:
                    last_sly_data = resp_obj["sly_data"]

                chat_context = resp_obj.get("chat_context", {})
                histories = chat_context.get("chat_histories", [])
                if histories:
                    messages = histories[-1].get("messages", [])
                    if messages:
                        text = messages[-1].get("text", "")
                        if text:
                            last_text = text

            except json.JSONDecodeError:
                continue

        # ── Classify the final response text ──
        if not last_text:
            logger.warning("No text extracted from streaming response — stream ended empty")
            return {
                "ok": False,
                "error_code": "empty_response",
                "msg": (
                    "The agent returned no response. This usually means the model's "
                    "context window was exceeded or the server hit its max_iterations "
                    "limit. Try a shorter or simpler request."
                ),
            }

        error_code, friendly_msg = _classify_response_text(last_text)
        if error_code:
            logger.warning("Agent response contains error pattern '%s': %s", error_code, last_text[:200])
            return {
                "ok": False,
                "error_code": error_code,
                "msg": friendly_msg,
            }

        logger.info("Agent response received: %d chars", len(last_text))
        return {
            "ok": True,
            "response": last_text,
            "sly_data": last_sly_data,
        }

    except requests.ConnectionError:
        logger.error("Cannot connect to Neuro SAN server at %s", BASE_URL)
        return {
            "ok": False,
            "error_code": "connection",
            "msg": (
                f"Cannot connect to Neuro SAN server at {BASE_URL}. "
                f"Start it with: python -m run --server-http-port {NEURO_SAN_PORT}"
            ),
        }
    except requests.Timeout:
        logger.error("Timeout calling Neuro SAN server (600s)")
        return {
            "ok": False,
            "error_code": "timeout",
            "msg": "Agent request timed out (10 minute limit). The pipeline may need more time — increase max_execution_seconds in the HOCON.",
        }
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 0
        logger.error("HTTP error from Neuro SAN: %s", e)
        if status == 429:
            return {"ok": False, "error_code": "rate_limit", "msg": "LLM API rate limit hit (HTTP 429). Wait a minute and retry."}
        if status >= 500:
            return {"ok": False, "error_code": "api_overloaded", "msg": f"Neuro SAN server error ({status}). The server may be overloaded."}
        return {"ok": False, "error_code": "http_error", "msg": f"Neuro SAN HTTP error: {e}"}
    except Exception as e:
        logger.error("Unexpected error invoking agent: %s", e)
        return {"ok": False, "error_code": "unknown", "msg": f"Unexpected error: {str(e)}"}


def check_server_health():
    """Check if the Neuro SAN server is reachable."""
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/list", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False
