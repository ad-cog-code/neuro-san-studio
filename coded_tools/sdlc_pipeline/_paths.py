"""
_paths.py — Shared path-resolution helpers for sdlc_pipeline CodedTools.

Every read/write is clamped to the project folder passed via sly_data
(or a small allow-list of secondary roots for Step 10 — neuro-san-studio).
This prevents agents from writing outside their own project.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any


# Secondary roots (besides project_folder) that agents are allowed to write to.
# Step 10 (neuro_ai_developer) writes HOCON + prompts under neuro-san-studio.
NEURO_SAN_STUDIO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)


def get_project_folder(sly_data: dict[str, Any]) -> str:
    """Return the project_folder from sly_data, or raise if missing."""
    folder = sly_data.get("project_folder") if sly_data else None
    if not folder:
        raise ValueError(
            "project_folder is missing from sly_data — AppMagic must pass it "
            "when calling Neuro SAN."
        )
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        # The folder may not yet exist on first write — create it.
        os.makedirs(folder, exist_ok=True)
    return folder


def resolve_safe_path(
    relative_path: str,
    sly_data: dict[str, Any],
    *,
    allow_neuro_san_studio: bool = False,
) -> str:
    """
    Resolve a relative path against the project folder (or neuro-san-studio
    when allow_neuro_san_studio=True). Refuses absolute paths and ".." escapes.
    """
    if not relative_path:
        raise ValueError("path is empty")

    # Allow callers to opt in to writing under neuro-san-studio (Step 10 only).
    if allow_neuro_san_studio and relative_path.startswith("neuro-san-studio/"):
        sub = relative_path[len("neuro-san-studio/"):]
        candidate = os.path.abspath(os.path.join(NEURO_SAN_STUDIO_ROOT, sub))
        if not candidate.startswith(NEURO_SAN_STUDIO_ROOT + os.sep) and candidate != NEURO_SAN_STUDIO_ROOT:
            raise ValueError(f"path escapes neuro-san-studio root: {relative_path}")
        return candidate

    # Reject absolute paths and parent-directory escapes for project paths.
    if os.path.isabs(relative_path):
        raise ValueError(f"absolute paths are not allowed: {relative_path}")

    project_folder = get_project_folder(sly_data)
    candidate = os.path.abspath(os.path.join(project_folder, relative_path))
    if not candidate.startswith(project_folder + os.sep) and candidate != project_folder:
        raise ValueError(f"path escapes project folder: {relative_path}")
    return candidate


def append_tool_log(
    sly_data: dict[str, Any],
    *,
    tool: str,
    agent: str | None,
    path: str,
    status: str,
    detail: str = "",
) -> None:
    """
    Append a one-line entry to <project_folder>/logs/tool_calls.log.
    Best-effort — never raises (a logging failure must not crash a tool call).
    """
    try:
        project_folder = get_project_folder(sly_data)
    except Exception:
        return
    try:
        log_dir = os.path.join(project_folder, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "tool_calls.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        agent_str = agent or "-"
        line = f"{timestamp}  {tool:10s}  agent={agent_str:24s}  {status:6s}  {path}"
        if detail:
            line += f"  | {detail}"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
