"""
coded_tools/common/read_docx.py
════════════════════════════════
ReadDocx — extract text from a Word (.docx) file.

Returns document text with structural markers:
  • Headings   → "# / ## / ###" prefix
  • Tables     → pipe-separated rows  |col1|col2|col3|
  • Paragraphs → plain text

Supports paragraph-range slicing (start_para / end_para) for large documents.
When truncated, the response tells the agent exactly what to call next.

Path resolution:
  • Relative paths → resolved against input_dir (sly_data)
  • Absolute paths → used as-is (Flask upload folders)

HOCON class reference
──────────────────────
    "class": "coded_tools.common.read_docx.ReadDocx"

HOCON tool block (copy-paste into any network)
───────────────────────────────────────────────
    {
        "name": "read_docx",
        "class": "coded_tools.common.read_docx.ReadDocx",
        "function": {
            "description": "Extract text from a Word (.docx) file. Returns headings, paragraphs, and tables as structured plain text. Use start_para/end_para for large documents — the response tells you the next start_para when truncated.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path":       { "type": "string",  "description": "DOCX path. Relative to input_dir, or absolute." },
                    "start_para": { "type": "integer", "description": "1-based paragraph block to start from (optional). Counts headings, paragraphs, and tables." },
                    "end_para":   { "type": "integer", "description": "1-based paragraph block to stop at, inclusive (optional)." },
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

import asyncio
import logging
import os
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool
from coded_tools.common._base import log_call, resolve_input_path

logger = logging.getLogger(__name__)

MAX_RETURN_BYTES = 64_000


def _heading_prefix(style_name: str) -> str:
    name = (style_name or "").lower()
    if "heading 1" in name: return "# "
    if "heading 2" in name: return "## "
    if "heading 3" in name: return "### "
    if "heading"   in name: return "#### "
    return ""


class ReadDocx(CodedTool):

    def invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        try:
            from docx import Document           # type: ignore
        except ImportError:
            return "Error: python-docx is not installed. Run: pip install python-docx"

        path_raw   = (args.get("path")  or "").strip()
        agent      = (args.get("agent") or "unknown-agent").strip()
        start_para = args.get("start_para")
        end_para   = args.get("end_para")

        if not path_raw:
            return "Error: read_docx requires 'path'."

        abs_path = resolve_input_path(path_raw, sly_data)

        if not os.path.exists(abs_path):
            log_call(sly_data, tool="ReadDocx", agent=agent, target=path_raw,
                     status="MISS", detail="file not found")
            return f"NOT_FOUND: '{path_raw}' does not exist."

        if not abs_path.lower().endswith(".docx"):
            return f"Error: '{path_raw}' does not appear to be a .docx file."

        try:
            doc = Document(abs_path)
            # Collect all blocks (paragraphs + tables) in document order
            blocks: list[str] = []
            table_count = 0

            for block in doc.element.body:
                tag = block.tag.split("}")[-1] if "}" in block.tag else block.tag

                if tag == "p":
                    from docx.text.paragraph import Paragraph  # type: ignore
                    para = Paragraph(block, doc)
                    text = para.text.strip()
                    if not text:
                        continue
                    prefix = _heading_prefix(para.style.name if para.style else "")
                    blocks.append(f"{prefix}{text}")

                elif tag == "tbl":
                    from docx.table import Table  # type: ignore
                    table = Table(block, doc)
                    table_count += 1
                    rows = [f"[Table {table_count}]"]
                    for row in table.rows:
                        cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                        rows.append("|" + "|".join(cells) + "|")
                    blocks.append("\n".join(rows))

        except Exception as exc:
            log_call(sly_data, tool="ReadDocx", agent=agent, target=path_raw,
                     status="ERROR", detail=str(exc))
            return f"Error: failed to read '{path_raw}': {exc}"

        total_blocks = len(blocks)

        # 1-based slice
        s = max(0, int(start_para) - 1) if start_para is not None else 0
        e = min(int(end_para), total_blocks) if end_para is not None else total_blocks
        sliced = start_para is not None or end_para is not None
        block_slice = blocks[s:e]

        content = "\n".join(block_slice)
        encoded = content.encode("utf-8")

        truncated    = False
        next_start: int | None = None

        if len(encoded) > MAX_RETURN_BYTES:
            cumulative = 0
            fits = 0
            for blk in block_slice:
                b = len(blk.encode("utf-8")) + 1
                if cumulative + b > MAX_RETURN_BYTES:
                    break
                cumulative += b
                fits += 1
            content    = "\n".join(block_slice[:fits])
            truncated  = True
            next_start = s + fits + 1   # 1-based

        detail = f"{total_blocks} blocks total ({table_count} tables)"
        if sliced:
            detail += f", blocks {s + 1}–{e}"
        if truncated:
            remaining = total_blocks - (s + fits)
            detail += f", truncated, next start_para={next_start}"
            content += (
                f"\n\n[TRUNCATED — {remaining} block(s) not shown. "
                f"Call again with start_para={next_start}"
                + (f", end_para={e}" if end_para is not None else "")
                + "]"
            )

        log_call(sly_data, tool="ReadDocx", agent=agent, target=path_raw,
                 status="OK", detail=detail)
        return content

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        return await asyncio.to_thread(self.invoke, args, sly_data)
