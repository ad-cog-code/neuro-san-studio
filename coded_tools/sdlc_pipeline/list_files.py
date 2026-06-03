"""
list_files.py — CodedTool for listing files under a project subfolder.

Agents use this to discover prior versions (e.g., is there a v2/ already?)
or to enumerate generated artifacts. Returns a newline-separated list of
relative paths.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.sdlc_pipeline._paths import (
    append_tool_log,
    get_project_folder,
    resolve_safe_path,
)

logger = logging.getLogger(__name__)


class ListFiles(CodedTool):
    """List files under `path` (relative to project folder), recursively."""

    async def async_invoke(
        self,
        args: dict[str, Any],
        sly_data: dict[str, Any],
    ) -> str:
        path = (args.get("path") or ".").strip()
        agent = (args.get("agent") or "").strip()
        target = (args.get("target") or "project").strip().lower()

        try:
            absolute_path = resolve_safe_path(
                path,
                sly_data,
                allow_neuro_san_studio=(target == "neuro_san_studio"),
            )
        except ValueError as e:
            append_tool_log(
                sly_data, tool="ListFiles", agent=agent, path=path,
                status="ERROR", detail=str(e),
            )
            return f"Error: {e}"

        if not os.path.exists(absolute_path):
            append_tool_log(
                sly_data, tool="ListFiles", agent=agent, path=path,
                status="MISS", detail="not found",
            )
            return f"EMPTY: {path} (folder does not exist)"

        if os.path.isfile(absolute_path):
            append_tool_log(
                sly_data, tool="ListFiles", agent=agent, path=path,
                status="OK", detail="single file",
            )
            return path

        try:
            project_folder = get_project_folder(sly_data)
        except ValueError as e:
            return f"Error: {e}"

        rows: list[str] = []
        for root, _dirs, files in os.walk(absolute_path):
            for filename in sorted(files):
                full = os.path.join(root, filename)
                rel = os.path.relpath(full, project_folder).replace("\\", "/")
                rows.append(rel)

        append_tool_log(
            sly_data, tool="ListFiles", agent=agent, path=path,
            status="OK", detail=f"{len(rows)} files",
        )
        logger.info("ListFiles: %s (%d files)", absolute_path, len(rows))
        if not rows:
            return f"EMPTY: {path} (no files)"
        return "\n".join(rows)
