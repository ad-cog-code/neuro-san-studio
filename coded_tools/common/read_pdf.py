"""
coded_tools/common/read_pdf.py
═══════════════════════════════
ReadPdf — extract text from a PDF file.

Uses pdfplumber. Page breaks marked with "--- Page N ---".
Use start_page / end_page to read large PDFs in sections.
When truncated, the response tells the agent exactly what to call next.

Path resolution:
  • Relative paths → resolved against input_dir (sly_data)
  • Absolute paths → used as-is (Flask upload folders)

HOCON class reference
──────────────────────
    "class": "coded_tools.common.read_pdf.ReadPdf"

HOCON tool block (copy-paste into any network)
───────────────────────────────────────────────
    {
        "name": "read_pdf",
        "class": "coded_tools.common.read_pdf.ReadPdf",
        "function": {
            "description": "Extract text from a PDF file. Returns text with page markers. Use start_page/end_page for large PDFs — the response tells you the next start_page when truncated.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path":       { "type": "string",  "description": "PDF path. Relative to input_dir, or absolute." },
                    "start_page": { "type": "integer", "description": "1-based page to start from (optional)." },
                    "end_page":   { "type": "integer", "description": "1-based page to stop at, inclusive (optional)." },
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


class ReadPdf(CodedTool):

    def invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        try:
            import pdfplumber  # type: ignore
        except ImportError:
            return "Error: pdfplumber is not installed. Run: pip install pdfplumber"

        path_raw   = (args.get("path")  or "").strip()
        agent      = (args.get("agent") or "unknown-agent").strip()
        start_page = args.get("start_page")
        end_page   = args.get("end_page")

        if not path_raw:
            return "Error: read_pdf requires 'path'."

        abs_path = resolve_input_path(path_raw, sly_data)

        if not os.path.exists(abs_path):
            log_call(sly_data, tool="ReadPdf", agent=agent, target=path_raw,
                     status="MISS", detail="file not found")
            return f"NOT_FOUND: '{path_raw}' does not exist."

        if not abs_path.lower().endswith(".pdf"):
            return f"Error: '{path_raw}' does not appear to be a PDF file."

        try:
            with pdfplumber.open(abs_path) as pdf:
                total_pages = len(pdf.pages)
                s = max(0, int(start_page) - 1) if start_page is not None else 0
                e = min(int(end_page), total_pages) if end_page is not None else total_pages

                parts = []
                for i, page in enumerate(pdf.pages[s:e], start=s + 1):
                    text = page.extract_text() or ""
                    parts.append(f"--- Page {i} ---\n{text}")

        except Exception as exc:
            log_call(sly_data, tool="ReadPdf", agent=agent, target=path_raw,
                     status="ERROR", detail=str(exc))
            return f"Error: failed to read PDF '{path_raw}': {exc}"

        content = "\n\n".join(parts)
        encoded = content.encode("utf-8")

        truncated    = False
        last_page_in = e   # last page index (1-based) actually included before truncation

        if len(encoded) > MAX_RETURN_BYTES:
            # Binary-search for the page that fits
            fits = 0
            cumulative = 0
            for part in parts:
                b = len(part.encode("utf-8")) + 2   # +2 for "\n\n"
                if cumulative + b > MAX_RETURN_BYTES:
                    break
                cumulative += b
                fits += 1
            content      = "\n\n".join(parts[:fits])
            last_page_in = s + fits   # 1-based last page included
            truncated    = True

        sliced = start_page is not None or end_page is not None
        detail = f"{total_pages} pages total"
        if sliced:
            detail += f", requested pages {s + 1}–{e}"
        if truncated:
            next_p = last_page_in + 1
            remaining = e - last_page_in
            detail += f", truncated after page {last_page_in}"
            content += (
                f"\n\n[TRUNCATED — {remaining} page(s) not shown. "
                f"Call again with start_page={next_p}"
                + (f", end_page={e}" if end_page is not None else "")
                + "]"
            )

        log_call(sly_data, tool="ReadPdf", agent=agent, target=path_raw,
                 status="OK", detail=detail)
        return content

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        return await asyncio.to_thread(self.invoke, args, sly_data)
