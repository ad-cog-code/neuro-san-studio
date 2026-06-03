"""
read_file.py — CodedTool for reading a file inside a project folder.

Agents use this to load prior artifacts (e.g., business_analyst reads
docs/requirements/v1/requirements-spec.md), the audit log, or sections
between <<<startforagent:NAME>>> ... <<<endforagent:NAME>>> markers.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.sdlc_pipeline._paths import append_tool_log, resolve_safe_path

logger = logging.getLogger(__name__)

# Cap: even if the file is huge, we never return more than this many bytes.
# Keeps the LLM context manageable. Agents that need more should slice by
# `for_agent` or `start`/`length`.
MAX_RETURN_BYTES = 64_000


class ReadFile(CodedTool):
    """Read `path` (relative to project folder) and return its content."""

    async def async_invoke(
        self,
        args: dict[str, Any],
        sly_data: dict[str, Any],
    ) -> str:
        path = (args.get("path") or "").strip()
        agent = (args.get("agent") or "").strip()
        for_agent = (args.get("for_agent") or "").strip()
        target = (args.get("target") or "project").strip().lower()

        if not path:
            return "Error: ReadFile requires 'path'."

        try:
            absolute_path = resolve_safe_path(
                path,
                sly_data,
                allow_neuro_san_studio=(target == "neuro_san_studio"),
            )
        except ValueError as e:
            append_tool_log(
                sly_data, tool="ReadFile", agent=agent, path=path,
                status="ERROR", detail=str(e),
            )
            return f"Error: {e}"

        if not os.path.exists(absolute_path):
            append_tool_log(
                sly_data, tool="ReadFile", agent=agent, path=path,
                status="MISS", detail="not found",
            )
            return f"NOT_FOUND: {path}"

        try:
            with open(absolute_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            append_tool_log(
                sly_data, tool="ReadFile", agent=agent, path=path,
                status="ERROR", detail=str(e),
            )
            logger.exception("ReadFile failed for %s", path)
            return f"Error: failed to read {path}: {e}"

        # Optionally slice to a specific agent's section.
        sliced = False
        if for_agent:
            pattern = (
                r'<<<startforagent:' + re.escape(for_agent) + r'>>>'
                r'(.*?)'
                r'<<<endforagent:' + re.escape(for_agent) + r'>>>'
            )
            m = re.search(pattern, content, re.DOTALL)
            if m:
                content = m.group(1).strip()
                sliced = True
            else:
                append_tool_log(
                    sly_data, tool="ReadFile", agent=agent, path=path,
                    status="MISS", detail=f"section for_agent={for_agent} not found",
                )
                return f"NOT_FOUND: section for_agent={for_agent} in {path}"

        truncated = False
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_RETURN_BYTES:
            content = encoded[:MAX_RETURN_BYTES].decode("utf-8", errors="ignore")
            truncated = True

        detail_bits = [f"{len(encoded)} bytes"]
        if sliced:
            detail_bits.append(f"sliced for_agent={for_agent}")
        if truncated:
            detail_bits.append(f"truncated to {MAX_RETURN_BYTES}")
        append_tool_log(
            sly_data, tool="ReadFile", agent=agent, path=path,
            status="OK", detail=", ".join(detail_bits),
        )
        logger.info("ReadFile: %s (%d bytes)", absolute_path, len(encoded))
        return content
