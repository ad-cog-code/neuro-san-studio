"""
start_neuro_san.py — Start LiteLLM proxy then Neuro SAN server.

Guarantees that the LiteLLM proxy (port 4000) is running before Neuro SAN
starts, so all agent networks get automatic Sonnet → Haiku fallback.

Run this INSTEAD of `python -m run` when launching Neuro SAN manually
OR from any Flask app that needs Neuro SAN (AppMagic, BidMagic, etc.).

USAGE
-----
    python start_neuro_san.py                   # default port 8080
    python start_neuro_san.py --http-port 8081  # custom HTTP port

WHAT IT DOES
------------
1. Checks if LiteLLM proxy is healthy at http://localhost:4000 — starts it if not.
   (Uses shared litellm_health.py at C:\\my-projects\\)
   Proxy lives at: C:\\my-projects\\litellm-proxy\\
2. Starts Neuro SAN via `python -m run` (any extra args forwarded).
3. On Ctrl+C: stops Neuro SAN cleanly.

REQUIREMENTS
------------
    litellm-proxy must be configured (C:\\my-projects\\litellm-proxy\\.env).
    ANTHROPIC_API_KEY lives in the proxy — not here.
"""

import os
import sys
import subprocess

HERE       = os.path.dirname(os.path.abspath(__file__))
MYPROJECTS = os.path.dirname(HERE)   # C:\my-projects\

# ── Import shared LiteLLM health check ───────────────────────────────────────
if MYPROJECTS not in sys.path:
    sys.path.insert(0, MYPROJECTS)

from litellm_health import ensure_litellm_running  # type: ignore


def _start_neuro_san(extra_args: list[str]):
    """Run Neuro SAN in the foreground (blocks until Ctrl+C)."""
    cmd = [sys.executable, "-m", "run"] + extra_args
    print(f"[start] Starting Neuro SAN: {' '.join(cmd)}")
    print("[start] Press Ctrl+C to stop.\n")
    subprocess.run(cmd, cwd=HERE)


if __name__ == "__main__":
    extra = sys.argv[1:]   # e.g. --http-port 8081

    print("[start] Checking services...")
    ensure_litellm_running()

    try:
        _start_neuro_san(extra)
    except KeyboardInterrupt:
        print("\n[start] Neuro SAN stopped.")
