"""
coded_tools/common/read_file.py
════════════════════════════════
ReadFile — read a text file from the input directory.

Caps the return at 64 KB. Use start_line / end_line to read large files
in sections. When truncated, the response tells the agent exactly what
parameters to use on the next call.

Path resolution:
  • Relative paths → resolved against input_dir (sly_data)
  • Absolute paths → used as-is

HOCON class reference
──────────────────────
    "class": "coded_tools.common.read_file.ReadFile"

HOCON tool block (copy-paste into any network)
───────────────────────────────────────────────
    {
        "name": "read_file",
        "class": "coded_tools.common.read_file.ReadFile",
        "function": {
            "description": "Read a text file from the input directory. Returns content with line numbers. Use start_line/end_line to page through large files — the response will tell you the next start_line when truncated.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path":       { "type": "string",  "description": "File path. Relative to input_dir, or absolute." },
                    "start_line": { "type": "integer", "description": "1-based line to start reading from (optional)." },
                    "end_line":   { "type": "integer", "description": "1-based line to stop at, inclusive (optional)." },
                    "agent":      { "type": "string",  "description": "Calling agent name (audit log)." }
                },
                "required": ["path"]
            }
        }
    }

sly_data keys read
───────────────────
    input_dir      (preferred) — where relative paths are resolved
    workspace_dir  (fallback)
    project_folder (fallback)  — bidmagic/dealcraft compat
"""

from __future__ import annotations

import logging
import os
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool
from coded_tools.common._base import log_call, resolve_input_path

logger = logging.getLogger(__name__)

MAX_RETURN_BYTES = 64_000


class ReadFile(CodedTool):

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        path_raw   = (args.get("path")  or "").strip()
        agent      = (args.get("agent") or "unknown-agent").strip()
        start_line = args.get("start_line")
        end_line   = args.get("end_line")

        if not path_raw:
            return "Error: read_file requires 'path'."

        abs_path = resolve_input_path(path_raw, sly_data)

        if not os.path.exists(abs_path):
            log_call(sly_data, tool="ReadFile", agent=agent, target=path_raw,
                     status="MISS", detail="file not found")
            return f"NOT_FOUND: '{path_raw}' does not exist."

        if os.path.isdir(abs_path):
            return f"Error: '{path_raw}' is a directory. Use list_files to browse."

        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError as exc:
            log_call(sly_data, tool="ReadFile", agent=agent, target=path_raw,
                     status="ERROR", detail=str(exc))
            return f"Error: failed to read '{path_raw}': {exc}"

        total_lines = len(lines)

        # 1-based slice
        s = max(0, int(start_line) - 1) if start_line is not None else 0
        e = int(end_line)               if end_line   is not None else total_lines
        e = min(e, total_lines)
        sliced = (start_line is not None or end_line is not None)
        lines_slice = lines[s:e]

        content = "".join(lines_slice)
        encoded = content.encode("utf-8")

        truncated = False
        next_start: int | None = None

        if len(encoded) > MAX_RETURN_BYTES:
            # Find how many lines fit within the byte cap
            cumulative = 0
            fits = 0
            for ln in lines_slice:
                b = len(ln.encode("utf-8"))
                if cumulative + b > MAX_RETURN_BYTES:
                    break
                cumulative += b
                fits += 1
            content   = "".join(lines_slice[:fits])
            truncated = True
            next_start = s + fits + 1   # 1-based

        detail_parts = [f"{total_lines} lines total"]
        if sliced:
            detail_parts.append(f"lines {s + 1}–{e}")
        if truncated:
            detail_parts.append(f"truncated, next start_line={next_start}")

        if truncated:
            remaining = total_lines - (s + fits)
            content += (
                f"\n\n[TRUNCATED — {remaining} lines not shown. "
                f"Call again with start_line={next_start}"
                + (f", end_line={e}" if end_line is not None else "")
                + "]"
            )

        log_call(sly_data, tool="ReadFile", agent=agent, target=path_raw,
                 status="OK", detail=", ".join(detail_parts))
        return content
