"""
coded_tools/common/convert_to_pdf.py
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
ConvertToPdf â€” convert a DOCX file to PDF using Microsoft Word (Windows).

Uses the docx2pdf library which drives the Word COM API on Windows,
producing pixel-perfect PDF output identical to "Save As PDF" in Word.

Typical workflow for agents:
    1. write_docx  â†’ create outputs/report.docx
    2. convert_to_pdf â†’ convert to outputs/report.pdf
    3. Return the PDF path to the Flask app for download

Path resolution:
  â€¢ Relative input paths  â†’ resolved against workspace
  â€¢ Absolute input paths  â†’ used as-is (DOCX from Flask upload folders)
  â€¢ Relative output paths â†’ resolved against workspace (auto-creates parent dirs)
  â€¢ If output_path is omitted â†’ PDF saved alongside the DOCX (same folder, .pdf extension)

Requirements:
  â€¢ Microsoft Word must be installed (uses Word COM API on Windows)
  â€¢ docx2pdf>=0.1.8   (pip install docx2pdf)
  â€¢ Windows only â€” on Linux/Mac use LibreOffice headless instead

HOCON class reference
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "class": "coded_tools.common.convert_to_pdf.ConvertToPdf"

HOCON tool block (copy-paste into any network)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "name": "convert_to_pdf",
        "class": "coded_tools.common.convert_to_pdf.ConvertToPdf",
        "function": {
            "description": "Convert a Word (.docx) file to PDF using Microsoft Word. Requires Word to be installed on the server. Input can be workspace-relative or absolute path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to the source .docx file. Workspace-relative or absolute."
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional path for the output .pdf file. Workspace-relative. If omitted, PDF is saved in the same folder as the DOCX with a .pdf extension."
                    },
                    "agent": {
                        "type": "string",
                        "description": "Name of the calling agent (used in audit log)."
                    }
                },
                "required": ["input_path"]
            }
        }
    }

sly_data keys read
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    input_dir      (preferred) â€” resolves relative input paths
    output_dir     (preferred) â€” resolves relative output paths
    workspace_dir  (fallback for both)
    project_folder (fallback)  â€” bidmagic/dealcraft compat
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.common._base import get_output_dir, log_call, resolve_input_path, resolve_output_path

logger = logging.getLogger(__name__)


class ConvertToPdf(CodedTool):
    """Convert a DOCX file to PDF using Microsoft Word (Windows COM API)."""

    def invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        try:
            from docx2pdf import convert  # type: ignore
        except ImportError:
            return (
                "Error: docx2pdf is not installed. Run: pip install docx2pdf\n"
                "Also ensure Microsoft Word is installed on this machine."
            )

        input_raw  = (args.get("input_path")  or "").strip()
        output_raw = (args.get("output_path") or "").strip() or None
        agent      = (args.get("agent")       or "unknown-agent").strip()

        if not input_raw:
            return "Error: convert_to_pdf requires 'input_path'."

        # Resolve input path (absolute allowed for Flask uploads)
        abs_input = resolve_input_path(input_raw, sly_data)

        if not os.path.exists(abs_input):
            log_call(sly_data, tool="ConvertToPdf", agent=agent, target=input_raw,
                     status="MISS", detail="input file not found")
            return f"NOT_FOUND: '{input_raw}' does not exist."

        if not abs_input.lower().endswith(".docx"):
            return f"Error: convert_to_pdf only supports .docx input (got '{input_raw}')."

        # Resolve output path
        if output_raw:
            try:
                abs_output = resolve_output_path(output_raw, sly_data)
            except ValueError as exc:
                return f"Error: {exc}"
            if not abs_output.lower().endswith(".pdf"):
                abs_output = abs_output + ".pdf"
            os.makedirs(os.path.dirname(abs_output), exist_ok=True)
        else:
            # Same folder as input, .pdf extension
            abs_output = os.path.splitext(abs_input)[0] + ".pdf"

        logger.debug("ConvertToPdf: %s â†’ %s", abs_input, abs_output)

        try:
            convert(abs_input, abs_output)
        except Exception as exc:
            log_call(sly_data, tool="ConvertToPdf", agent=agent, target=input_raw,
                     status="ERROR", detail=str(exc))
            logger.exception("ConvertToPdf failed: %s â†’ %s", abs_input, abs_output)
            return (
                f"Error: conversion failed: {exc}\n"
                "Ensure Microsoft Word is installed and not currently blocking the file."
            )

        if not os.path.exists(abs_output):
            log_call(sly_data, tool="ConvertToPdf", agent=agent, target=input_raw,
                     status="ERROR", detail="PDF not created â€” Word conversion returned no error but file missing")
            return f"Error: conversion appeared to succeed but PDF was not created at '{abs_output}'."

        pdf_size = os.path.getsize(abs_output)

        # Return an output_dir-relative path if possible, else absolute
        try:
            output_dir = get_output_dir(sly_data)
            display_output = os.path.relpath(abs_output, output_dir)
        except ValueError:
            display_output = abs_output

        log_call(sly_data, tool="ConvertToPdf", agent=agent, target=input_raw,
                 status="OK", detail=f"â†’ {display_output} ({pdf_size} bytes)")
        logger.debug("ConvertToPdf: OK  %s (%d bytes)", display_output, pdf_size)

        return f"OK: converted '{input_raw}' â†’ '{display_output}' ({pdf_size} bytes)."

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        return await asyncio.to_thread(self.invoke, args, sly_data)

