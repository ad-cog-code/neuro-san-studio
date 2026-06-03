"""
coded_tools/common/write_file.py
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
WriteFile â€” write or append content to a file inside the workspace.

Chunked-write pattern for large outputs
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
LLM tool-call output is typically limited to ~8 KB per call.
For large documents, agents should split at section boundaries:

    call 1 â†’ write_file(path=..., content=chunk1, mode="write")
    call 2 â†’ write_file(path=..., content=chunk2, mode="append")
    ...

A WARN is logged (but not raised) for chunks > 15 KB.
Keep each chunk â‰¤ 8 000 chars.

HOCON class reference
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "class": "coded_tools.common.write_file.WriteFile"

HOCON tool block (copy-paste into any network)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "name": "write_file",
        "class": "coded_tools.common.write_file.WriteFile",
        "function": {
            "description": "Write or append content to a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file inside the workspace."
                    },
                    "content": {
                        "type": "string",
                        "description": "Text content to write or append."
                    },
                    "mode": {
                        "type": "string",
                        "description": "'write' (default, overwrites) or 'append' (adds to end)."
                    },
                    "agent": {
                        "type": "string",
                        "description": "Name of the calling agent (used in audit log)."
                    }
                },
                "required": ["path", "content"]
            }
        }
    }

sly_data keys read
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    output_dir     (preferred) â€” where relative paths are resolved for writes
    workspace_dir  (fallback)
    project_folder (fallback)  â€” bidmagic/dealcraft compat
"""

from __future__ import annotations

import logging
import os
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.common._base import log_call, resolve_path

logger = logging.getLogger(__name__)

SOFT_CHUNK_LIMIT = 15_000   # bytes â€” WARN but don't reject


class WriteFile(CodedTool):
    """Write or append *content* to *path* (relative to workspace root)."""

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        path     = (args.get("path")    or "").strip()
        content  =  args.get("content")
        mode_raw = (args.get("mode")    or "write").strip().lower()
        agent    = (args.get("agent")   or "unknown-agent").strip()

        if not path:
            return "Error: write_file requires 'path'."
        if content is None:
            return "Error: write_file requires 'content'."
        if mode_raw not in ("write", "append"):
            return f"Error: 'mode' must be 'write' or 'append' (got {mode_raw!r})."

        try:
            abs_path = resolve_path(path, sly_data)
        except ValueError as exc:
            log_call(sly_data, tool="WriteFile", agent=agent, target=path,
                     status="ERROR", detail=str(exc))
            return f"Error: {exc}"

        # append to non-existent file â†’ treat as fresh write
        file_existed = os.path.isfile(abs_path)
        if mode_raw == "append" and not file_existed:
            open_mode, mode_note = "w", "append-as-create"
        elif mode_raw == "append":
            open_mode, mode_note = "a", "append"
        else:
            open_mode, mode_note = "w", "write"

        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, open_mode, encoding="utf-8") as fh:
                fh.write(content)
            chunk_bytes = len(content.encode("utf-8"))
            total_bytes = os.path.getsize(abs_path)
        except OSError as exc:
            log_call(sly_data, tool="WriteFile", agent=agent, target=path,
                     status="ERROR", detail=f"{mode_note}: {exc}")
            logger.exception("WriteFile failed for %s", path)
            return f"Error: failed to write '{path}': {exc}"

        size_warn = ""
        if chunk_bytes > SOFT_CHUNK_LIMIT:
            size_warn = " [WARN: chunk >15 KB â€” split at section boundaries using mode='append']"
            logger.warning("WriteFile: chunk %dB exceeds soft limit for %s", chunk_bytes, path)

        log_call(sly_data, tool="WriteFile", agent=agent, target=path, status="OK",
                 detail=f"{mode_note}: +{chunk_bytes}B (file now {total_bytes}B){size_warn}")
        logger.debug("WriteFile: %s  mode=%s  chunk=%dB  total=%dB", path, mode_note, chunk_bytes, total_bytes)

        verb = "appended to" if (mode_raw == "append" and file_existed) else "wrote"
        return f"OK: {verb} '{path}' (+{chunk_bytes} bytes, file now {total_bytes} bytes total).{size_warn}"

