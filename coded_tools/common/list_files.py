"""
coded_tools/common/list_files.py
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
ListFiles â€” list files inside the agent's input or output directory.

Returns a newline-separated list of relative paths. Useful for:
  â€¢ Discovering what input files exist before reading them.
  â€¢ Verifying which output files have already been written.
  â€¢ Browsing sub-directories produced by earlier agents.

Use `dir="input"` (default) to browse uploaded/input files.
Use `dir="output"` to browse files the agents have written.

HOCON class reference
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "class": "coded_tools.common.list_files.ListFiles"

HOCON tool block (copy-paste into any network)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "name": "list_files",
        "class": "coded_tools.common.list_files.ListFiles",
        "function": {
            "description": "List files inside the input or output directory. Returns relative paths. Use dir='input' (default) to see uploaded files; dir='output' to see generated files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path":    { "type": "string", "description": "Sub-path to list within the chosen directory. Defaults to '.' (root of that directory)." },
                    "dir":     { "type": "string", "description": "'input' (default â€” browse uploaded/input files) or 'output' (browse generated output files)." },
                    "pattern": { "type": "string", "description": "Optional glob-style filter, e.g. '*.pdf', '*.md'. Defaults to all files." },
                    "agent":   { "type": "string", "description": "Calling agent name (audit log)." }
                }
            }
        }
    }

sly_data keys read
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    input_dir      (preferred for dir="input")  â€” where uploaded/input files live
    output_dir     (preferred for dir="output") â€” where agents write results
    workspace_dir  (fallback for both)
    project_folder (fallback)  â€” bidmagic/dealcraft compat
"""

from __future__ import annotations

import fnmatch
import logging
import os
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.common._base import get_input_dir, get_output_dir, log_call

logger = logging.getLogger(__name__)

MAX_FILES = 500   # safety cap â€” avoid flooding the LLM context window


class ListFiles(CodedTool):
    """List files under *path* (relative to the chosen input or output directory)."""

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        path     = (args.get("path")    or ".").strip()
        dir_side = (args.get("dir")     or "input").strip().lower()
        pattern  = (args.get("pattern") or "").strip()
        agent    = (args.get("agent")   or "unknown-agent").strip()

        if dir_side not in ("input", "output"):
            return f"Error: 'dir' must be 'input' or 'output' (got '{dir_side}')."

        base_dir = get_input_dir(sly_data) if dir_side == "input" else get_output_dir(sly_data)

        # Resolve path relative to base_dir (no escaping allowed)
        if os.path.isabs(path):
            log_call(sly_data, tool="ListFiles", agent=agent, target=path,
                     status="ERROR", detail="absolute paths not allowed â€” use a relative sub-path")
            return "Error: 'path' must be relative (e.g. '.' or 'uploads/pdf/')."

        abs_path = os.path.normpath(os.path.join(base_dir, path))
        if not abs_path.startswith(base_dir):
            return "Error: 'path' escapes the directory â€” '..' traversal not allowed."

        if not os.path.exists(abs_path):
            log_call(sly_data, tool="ListFiles", agent=agent, target=path,
                     status="MISS", detail=f"{dir_side} path not found")
            return f"EMPTY: '{path}' does not exist in the {dir_side} directory."

        if os.path.isfile(abs_path):
            log_call(sly_data, tool="ListFiles", agent=agent, target=path,
                     status="OK", detail="single file")
            return os.path.relpath(abs_path, base_dir).replace("\\", "/")

        rows: list[str] = []
        capped = False

        for root, _dirs, files in os.walk(abs_path):
            for filename in sorted(files):
                if pattern and not fnmatch.fnmatch(filename, pattern):
                    continue
                full = os.path.join(root, filename)
                rel  = os.path.relpath(full, base_dir).replace("\\", "/")
                rows.append(rel)
                if len(rows) >= MAX_FILES:
                    capped = True
                    break
            if capped:
                break

        if not rows:
            log_call(sly_data, tool="ListFiles", agent=agent, target=path,
                     status="OK", detail=f"empty ({dir_side})")
            return (
                f"EMPTY: '{path}' exists in the {dir_side} directory "
                f"but contains no files{' matching ' + pattern if pattern else ''}."
            )

        if capped:
            rows.append(f"[WARNING: listing capped at {MAX_FILES} â€” use a sub-path or pattern to narrow results]")

        log_call(sly_data, tool="ListFiles", agent=agent, target=path,
                 status="OK", detail=f"{len(rows)} files, dir={dir_side}" + (f", pattern={pattern}" if pattern else ""))
        logger.debug("ListFiles: %s/%s (%d entries)", dir_side, path, len(rows))
        return "\n".join(rows)

