"""
run_command.py — CodedTool: run a shell command in the project folder.

Used exclusively by app_finisher to test-run the generated app, capture
errors, fix them, and re-run — the run→fix→run loop.

Behaviour for long-running processes (Flask apps)
--------------------------------------------------
Flask never exits on its own. This tool uses Popen + a short timeout
to detect STARTUP errors vs. successful startup:

  - Process exits quickly (returncode != 0) → startup error. Return full stderr.
  - Process still running after `timeout` seconds AND stderr has no Python
    tracebacks → "APP_STARTUP_OK". Kill the process, return success message.
  - Process still running but stderr has tracebacks → return the error lines.

Typical usage by app_finisher:
  1. run_command("python app.py", timeout=15)
  2. If APP_STARTUP_OK → done.
  3. If error → read the traceback, fix the file, call run_command again.
  4. Repeat up to 5 times.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.sdlc_pipeline._paths import append_tool_log, get_project_folder

logger = logging.getLogger(__name__)

# Lines in Flask startup stderr that are NOT errors (safe to ignore)
FLASK_NOISE = frozenset([
    "serving flask app",
    "debug mode:",
    "warning: this is a development server",
    "running on http",
    "press ctrl+c to quit",
    "restarting with",
    "debugger is active",
    "debugger pin:",
])

MAX_OUTPUT_CHARS = 3000


def _is_flask_noise(line: str) -> bool:
    low = line.strip().lower()
    return any(low.startswith(noise) for noise in FLASK_NOISE)


def _extract_errors(text: str) -> str:
    """Return lines that look like real errors, truncated to MAX_OUTPUT_CHARS."""
    error_lines = [ln for ln in text.splitlines() if not _is_flask_noise(ln)]
    joined = "\n".join(error_lines).strip()
    if len(joined) > MAX_OUTPUT_CHARS:
        joined = joined[:MAX_OUTPUT_CHARS] + "\n...[truncated]"
    return joined


class RunCommand(CodedTool):
    """Run a shell command in the project folder and return its output."""

    async def async_invoke(
        self,
        args: dict[str, Any],
        sly_data: dict[str, Any],
    ) -> str:
        command = (args.get("command") or "").strip()
        agent   = (args.get("agent") or "app_finisher").strip()
        timeout = int(args.get("timeout") or 15)

        if not command:
            return "Error: RunCommand requires 'command'."

        try:
            project_folder = get_project_folder(sly_data)
        except ValueError as e:
            return f"Error: {e}"

        env = {**os.environ, "PYTHONPATH": project_folder}

        append_tool_log(
            sly_data, tool="RunCommand", agent=agent,
            path=command, status="STARTING",
            detail=f"cwd={project_folder} timeout={timeout}s",
        )

        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=project_folder,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )

            try:
                stdout, stderr = proc.communicate(timeout=timeout)
                exit_code = proc.returncode

                # Process exited before timeout — almost certainly a crash
                errors = _extract_errors(stderr + stdout)
                status_msg = f"EXIT CODE: {exit_code}"
                if exit_code != 0 or errors:
                    result = f"{status_msg}\nERRORS:\n{errors}" if errors else status_msg
                else:
                    result = f"{status_msg}\n{stdout.strip()[:1000]}"

            except subprocess.TimeoutExpired:
                # Process still running — read what's been written so stderr/stdout
                proc.kill()
                stdout, stderr = proc.communicate()

                errors = _extract_errors(stderr + stdout)
                if errors:
                    result = (
                        f"PROCESS STILL RUNNING after {timeout}s but errors detected:\n"
                        f"{errors}"
                    )
                else:
                    result = (
                        f"APP_STARTUP_OK: process ran for {timeout}s with no "
                        f"Python errors. The app started successfully."
                    )

        except Exception as exc:
            result = f"RunCommand failed: {exc}"

        append_tool_log(
            sly_data, tool="RunCommand", agent=agent,
            path=command, status="DONE",
            detail=result[:200],
        )
        return result
