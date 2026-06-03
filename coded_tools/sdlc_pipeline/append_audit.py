"""
append_audit.py — CodedTool for appending an agent's contribution to the
project's audit-progress.md.

Each agent calls this once at the end of its turn. The block is wrapped in
<<<startforagent:NAME>>> ... <<<endforagent:NAME>>> markers so downstream
agents can ReadFile with for_agent=NAME to slice exactly what they need.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.sdlc_pipeline._paths import (
    append_tool_log,
    get_project_folder,
)

logger = logging.getLogger(__name__)

AUDIT_RELATIVE = os.path.join("docs", "audit-progress.md")


class AppendAudit(CodedTool):
    """Append a delimited entry to docs/audit-progress.md."""

    async def async_invoke(
        self,
        args: dict[str, Any],
        sly_data: dict[str, Any],
    ) -> str:
        agent = (args.get("agent") or "").strip()
        phase = (args.get("phase") or "").strip()
        entry = args.get("entry")

        if not agent:
            return "Error: AppendAudit requires 'agent'."
        if entry is None or not str(entry).strip():
            return "Error: AppendAudit requires non-empty 'entry'."

        try:
            project_folder = get_project_folder(sly_data)
        except ValueError as e:
            return f"Error: {e}"

        audit_path = os.path.join(project_folder, AUDIT_RELATIVE)
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        phase_line = f" — Phase: {phase}" if phase else ""
        block = (
            f"\n<<<startforagent:{agent}>>>\n"
            f"#### {agent}  *({timestamp}){phase_line}*\n"
            f"{str(entry).strip()}\n"
            f"<<<endforagent:{agent}>>>\n"
        )

        try:
            with open(audit_path, "a", encoding="utf-8") as f:
                f.write(block)
        except OSError as e:
            append_tool_log(
                sly_data, tool="AppendAudit", agent=agent, path=AUDIT_RELATIVE,
                status="ERROR", detail=str(e),
            )
            logger.exception("AppendAudit failed for %s", agent)
            return f"Error: failed to append audit entry: {e}"

        append_tool_log(
            sly_data, tool="AppendAudit", agent=agent, path=AUDIT_RELATIVE,
            status="OK", detail=f"phase={phase or '-'}",
        )
        logger.info("AppendAudit: appended block for %s", agent)
        return f"OK: audit entry appended for {agent}"
