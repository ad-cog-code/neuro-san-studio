"""
write_file.py — CodedTool for writing a file inside a project folder.

Supports chunked writes via the `mode` parameter:
  - mode="write"  (default) — overwrite/create the file with `content`
  - mode="append"           — append `content` to an existing file

Why chunking matters
--------------------
A large agent output (e.g. a 20 KB requirements-spec.md) cannot be reliably
emitted as a single tool_use payload — Claude's structured tool-call output
budget is smaller than its message budget, and the agent chain gets cancelled
when the model can't fit the whole `content` into one tool call. Splitting
into ~3-4 KB chunks via mode="append" keeps every tool call within budget.

Recommended chunk size: 3000-4000 chars per call. The first call uses
mode="write" (creates/overwrites); subsequent calls use mode="append".

Step 10 (neuro_ai_developer) also writes under neuro-san-studio — pass
`target="neuro_san_studio"` for those writes.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.sdlc_pipeline._paths import append_tool_log, resolve_safe_path

logger = logging.getLogger(__name__)

# Soft guidance only — we don't reject large writes, but we log a warning
# so problems show up clearly in the per-project tool_calls.log.
SOFT_CHUNK_LIMIT = 6000


class WriteFile(CodedTool):
    """Write or append `content` to a file path relative to the active project folder."""

    async def async_invoke(
        self,
        args: dict[str, Any],
        sly_data: dict[str, Any],
    ) -> str:
        path = (args.get("path") or "").strip()
        content = args.get("content")
        agent = (args.get("agent") or "").strip()
        target = (args.get("target") or "project").strip().lower()
        mode_arg = (args.get("mode") or "write").strip().lower()

        if not path:
            return "Error: WriteFile requires 'path'."
        if content is None:
            return "Error: WriteFile requires 'content'."

        if mode_arg not in ("write", "append"):
            return (
                f"Error: WriteFile 'mode' must be 'write' or 'append' "
                f"(got {mode_arg!r})."
            )

        try:
            absolute_path = resolve_safe_path(
                path,
                sly_data,
                allow_neuro_san_studio=(target == "neuro_san_studio"),
            )
        except ValueError as e:
            append_tool_log(
                sly_data, tool="WriteFile", agent=agent, path=path,
                status="ERROR", detail=str(e),
            )
            return f"Error: {e}"

        # mode="append" only makes sense if the file exists. If not, treat
        # as a soft create so the agent doesn't have to worry about ordering.
        file_existed = os.path.isfile(absolute_path)
        if mode_arg == "append" and not file_existed:
            effective_open_mode = "w"
            mode_note = "append-as-create"
        elif mode_arg == "append":
            effective_open_mode = "a"
            mode_note = "append"
        else:
            effective_open_mode = "w"
            mode_note = "write"

        try:
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            with open(absolute_path, effective_open_mode, encoding="utf-8") as f:
                f.write(content)
            chunk_bytes = len(content.encode("utf-8"))
            total_bytes = os.path.getsize(absolute_path)
        except OSError as e:
            append_tool_log(
                sly_data, tool="WriteFile", agent=agent, path=path,
                status="ERROR", detail=f"{mode_note}: {e}",
            )
            logger.exception("WriteFile failed for %s", path)
            return f"Error: failed to write {path}: {e}"

        # Soft warning if the agent crammed too much into one chunk.
        oversized = chunk_bytes > SOFT_CHUNK_LIMIT
        size_warn = " [WARN: chunk >6KB, split smaller next time]" if oversized else ""

        append_tool_log(
            sly_data, tool="WriteFile", agent=agent, path=path,
            status="OK",
            detail=f"{mode_note}: +{chunk_bytes}B (file now {total_bytes}B){size_warn}",
        )
        logger.info(
            "WriteFile: %s mode=%s chunk=%dB total=%dB",
            absolute_path, mode_note, chunk_bytes, total_bytes,
        )

        if mode_arg == "append" and file_existed:
            return f"OK: appended {chunk_bytes} bytes to {path} (file now {total_bytes} bytes)"
        return f"OK: wrote {path} ({chunk_bytes} bytes)"
