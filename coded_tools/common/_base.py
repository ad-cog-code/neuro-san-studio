"""
coded_tools/common/_base.py
════════════════════════════
Shared helpers for all common coded tools.

Directory resolution — Option A (input / output split)
────────────────────────────────────────────────────────
Each Flask app sets up to three keys in sly_data before calling Neuro SAN:

    sly_data = {
        "input_dir":  "/path/to/app/uploads",   # where agents READ from
        "output_dir": "/path/to/app/outputs",   # where agents WRITE to
        "workspace_dir": "/path/to/workspace",  # fallback for both
    }

Resolution order for READ tools (resolve_input_path):
  1. sly_data["input_dir"]      ← preferred; set to Flask uploads folder
  2. sly_data["workspace_dir"]  ← general workspace
  3. sly_data["project_folder"] ← bidmagic/dealcraft backward-compat
  4. env COMMON_INPUT_DIR
  5. env COMMON_WORKSPACE_DIR
  6. cwd (last resort — logged as warning)

Resolution order for WRITE tools (resolve_output_path):
  1. sly_data["output_dir"]     ← preferred; set to Flask outputs folder
  2. sly_data["workspace_dir"]  ← general workspace
  3. sly_data["project_folder"] ← bidmagic/dealcraft backward-compat
  4. env COMMON_OUTPUT_DIR
  5. env COMMON_WORKSPACE_DIR
  6. cwd (last resort — logged as warning)

Path rules
──────────
  READ  — relative paths resolved against input_dir.
          Absolute paths allowed (Flask upload folders outside workspace).
  WRITE — relative paths only; resolved against output_dir.
          Absolute paths and ".." traversal are rejected.
          Parent directories are auto-created on write.

Backward compatibility
──────────────────────
  Networks that only set workspace_dir (or project_folder) continue to work
  unchanged — input_dir and output_dir simply fall through to workspace_dir.

Audit log
─────────
  Every tool call appends a structured line to:
      <output_dir>/logs/tool_calls.log
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any


# ── Internal helper ───────────────────────────────────────────────────────────

def _first_set(*keys_and_env: str, sly_data: dict[str, Any], env_vars: list[str]) -> str:
    """Return the first non-empty value from sly_data keys, then env vars, then ''."""
    for key in keys_and_env:
        val = (sly_data or {}).get(key, "")
        if val and str(val).strip():
            return str(val).strip()
    for env in env_vars:
        val = os.getenv(env, "")
        if val and val.strip():
            return val.strip()
    return ""


# ── Directory resolution ──────────────────────────────────────────────────────

def get_input_dir(sly_data: dict[str, Any]) -> str:
    """
    Return the validated, absolute input directory.

    Priority: input_dir → workspace_dir → project_folder →
              COMMON_INPUT_DIR env → COMMON_WORKSPACE_DIR env → cwd
    """
    import logging
    logger = logging.getLogger(__name__)

    raw = _first_set(
        "input_dir", "workspace_dir", "project_folder",
        sly_data=sly_data,
        env_vars=["COMMON_INPUT_DIR", "COMMON_WORKSPACE_DIR"],
    )
    if not raw:
        cwd = os.getcwd()
        logger.warning(
            "input_dir not set in sly_data and COMMON_INPUT_DIR not set. "
            "Falling back to cwd: %s", cwd
        )
        raw = cwd

    d = os.path.abspath(str(raw))
    os.makedirs(d, exist_ok=True)
    return d


def get_output_dir(sly_data: dict[str, Any]) -> str:
    """
    Return the validated, absolute output directory.

    Priority: output_dir → workspace_dir → project_folder →
              COMMON_OUTPUT_DIR env → COMMON_WORKSPACE_DIR env → cwd
    """
    import logging
    logger = logging.getLogger(__name__)

    raw = _first_set(
        "output_dir", "workspace_dir", "project_folder",
        sly_data=sly_data,
        env_vars=["COMMON_OUTPUT_DIR", "COMMON_WORKSPACE_DIR"],
    )
    if not raw:
        cwd = os.getcwd()
        logger.warning(
            "output_dir not set in sly_data and COMMON_OUTPUT_DIR not set. "
            "Falling back to cwd: %s", cwd
        )
        raw = cwd

    d = os.path.abspath(str(raw))
    os.makedirs(d, exist_ok=True)
    return d


def get_workspace(sly_data: dict[str, Any]) -> str:
    """
    Backward-compatible alias — returns workspace_dir (or project_folder / cwd).
    New code should prefer get_input_dir / get_output_dir.
    """
    return get_output_dir(sly_data)


# ── Path resolution ───────────────────────────────────────────────────────────

def resolve_input_path(path: str, sly_data: dict[str, Any]) -> str:
    """
    Resolve a path for READ operations.

    • Absolute path → used as-is (allows Flask upload folders outside workspace)
    • Relative path → resolved against input_dir
    """
    p = (path or "").strip()
    if not p:
        raise ValueError("path is empty.")
    if os.path.isabs(p):
        return p
    return os.path.normpath(os.path.join(get_input_dir(sly_data), p))


def resolve_output_path(relative_path: str, sly_data: dict[str, Any]) -> str:
    """
    Resolve a relative path for WRITE operations against output_dir.

    Raises ValueError for:
      • empty path
      • absolute paths  (agents must use relative output paths)
      • ".." traversal that escapes the output sandbox
    """
    if not relative_path or not relative_path.strip():
        raise ValueError("path is empty — provide a relative path inside the output directory.")

    rp = relative_path.strip().replace("\\", "/")

    if os.path.isabs(rp):
        raise ValueError(
            f"Absolute output paths are not allowed: '{rp}'. "
            "Use a path relative to the output directory root."
        )

    output_dir = get_output_dir(sly_data)
    candidate  = os.path.abspath(os.path.join(output_dir, rp))

    if not (candidate.startswith(output_dir + os.sep) or candidate == output_dir):
        raise ValueError(
            f"Path '{rp}' escapes the output directory sandbox. "
            "Only paths inside the output directory are allowed."
        )
    return candidate


def resolve_path(relative_path: str, sly_data: dict[str, Any]) -> str:
    """
    Backward-compatible alias for resolve_output_path.
    Kept so existing tools that call resolve_path() continue to work.
    """
    return resolve_output_path(relative_path, sly_data)


# ── Audit logging ─────────────────────────────────────────────────────────────

def log_call(
    sly_data: dict[str, Any],
    *,
    tool: str,
    agent: str,
    target: str,
    status: str,
    detail: str = "",
) -> None:
    """
    Append one structured line to a tool_calls.log file.

    Log directory resolution order:
      1. sly_data["log_dir"]   ← explicit override; use for per-deal/per-iter logs
      2. <output_dir>/logs/    ← fallback (may be shared across all deals if
                                  output_dir is not scoped to a single run)

    Format:
        2026-05-27 10:30:00  WriteFile   agent=my-agent                    OK      some/path  | 512 bytes

    Failures are silently swallowed — logging must never crash a tool call.
    """
    try:
        explicit = sly_data.get("log_dir", "").strip()
        if explicit:
            log_dir = explicit
        else:
            log_dir = os.path.join(get_output_dir(sly_data), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "tool_calls.log")
        ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts}  {tool:<14s}  agent={agent:<30s}  {status:<6s}  {target}"
        if detail:
            line += f"  | {detail}"
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:   # noqa: BLE001
        pass            # never let logging kill a tool call
