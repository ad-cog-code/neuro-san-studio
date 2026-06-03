"""
coded_tools/common/ocr_image.py
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
OcrImage â€” extract text and details from an image using Claude vision.

Reads an image file and returns everything Claude can see in it: text,
labels, numbers, layout, captions, diagrams â€” whatever is present.

Powered by claude_ocr.py (shared module at C:\\my-projects\\claude_ocr.py).
Supported formats: .jpg / .jpeg / .png / .gif / .webp

Path resolution:
  â€¢ Relative paths  â†’ resolved against the workspace (same sandbox as read_file)
  â€¢ Absolute paths  â†’ used as-is (for images from Flask upload folders that live
                      outside the workspace, e.g. C:\\my-projects\\bidmagic\\uploads\\...)

HOCON class reference
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "class": "coded_tools.common.ocr_image.OcrImage"

HOCON tool block (copy-paste into any network)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "name": "ocr_image",
        "class": "coded_tools.common.ocr_image.OcrImage",
        "function": {
            "description": "Extract text and details from an image file using Claude AI vision. Supports PNG, JPG, GIF, WEBP. Returns everything visible: text, labels, numbers, diagrams, layout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the image file. Relative paths are resolved against the workspace. Absolute paths (e.g. from Flask uploads) are used as-is."
                    },
                    "model": {
                        "type": "string",
                        "description": "Claude model to use: 'haiku' (default â€” fast, cheap, good for clean screenshots), 'sonnet' (better for dense layouts, low-res scans, mixed content), 'opus' (best for handwriting, damaged docs, complex diagrams)."
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Custom extraction instruction. Default: extract all visible text preserving layout. Example: 'List every component and arrow in this architecture diagram'."
                    },
                    "agent": {
                        "type": "string",
                        "description": "Name of the calling agent (used in audit log)."
                    }
                },
                "required": ["path"]
            }
        }
    }

sly_data keys read
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    input_dir      (preferred) â€” where relative image paths are resolved
    workspace_dir  (fallback)
    project_folder (fallback)  â€” bidmagic/dealcraft compat

Environment
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ANTHROPIC_API_KEY  â€” must be set; used directly by claude_ocr.py
    (Does NOT use the LiteLLM proxy â€” vision calls go direct to Anthropic)
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.common._base import log_call, resolve_input_path

logger = logging.getLogger(__name__)

# â”€â”€ Locate the shared claude_ocr module (C:\my-projects\claude_ocr.py) â”€â”€â”€â”€â”€â”€â”€â”€
# coded_tools/common/ocr_image.py  â†’  ../../..  â†’  C:\my-projects\
_MYPROJECTS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _MYPROJECTS not in sys.path:
    sys.path.insert(0, _MYPROJECTS)

try:
    from claude_ocr import ocr_image as _ocr, MODEL_HAIKU, MODEL_SONNET, MODEL_OPUS  # type: ignore
    _OCR_AVAILABLE = True
except ImportError:
    _OCR_AVAILABLE = False
    MODEL_HAIKU = MODEL_SONNET = MODEL_OPUS = ""

_MODEL_MAP = {
    "haiku":  MODEL_HAIKU,
    "sonnet": MODEL_SONNET,
    "opus":   MODEL_OPUS,
}

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


class OcrImage(CodedTool):
    """Extract text and details from an image file using Claude vision."""

    def invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        if not _OCR_AVAILABLE:
            return (
                "Error: claude_ocr module not found. "
                f"Ensure claude_ocr.py exists at {_MYPROJECTS}\\claude_ocr.py"
            )

        path_raw = (args.get("path")   or "").strip()
        model_key = (args.get("model") or "haiku").strip().lower()
        prompt    =  args.get("prompt")
        agent     = (args.get("agent") or "unknown-agent").strip()

        if not path_raw:
            return "Error: ocr_image requires 'path'."

        # Resolve model name
        if model_key not in _MODEL_MAP:
            return (
                f"Error: unknown model '{model_key}'. "
                "Use 'haiku' (default), 'sonnet', or 'opus'."
            )
        model = _MODEL_MAP[model_key]

        # Resolve file path
        abs_path = resolve_input_path(path_raw, sly_data)
        path_label = path_raw  # for display / log

        # Validate
        if not os.path.exists(abs_path):
            log_call(sly_data, tool="OcrImage", agent=agent, target=path_label,
                     status="MISS", detail="file not found")
            return f"NOT_FOUND: '{path_raw}' does not exist."

        ext = os.path.splitext(abs_path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            log_call(sly_data, tool="OcrImage", agent=agent, target=path_label,
                     status="ERROR", detail=f"unsupported extension '{ext}'")
            return (
                f"Error: '{ext}' is not a supported image format. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        logger.debug("OcrImage: path=%s  model=%s  prompt=%r", abs_path, model, prompt)

        try:
            kwargs: dict[str, Any] = {"model": model}
            if prompt:
                kwargs["prompt"] = prompt
            text = _ocr(abs_path, **kwargs)
        except FileNotFoundError as exc:
            log_call(sly_data, tool="OcrImage", agent=agent, target=path_label,
                     status="MISS", detail=str(exc))
            return f"NOT_FOUND: {exc}"
        except ValueError as exc:
            log_call(sly_data, tool="OcrImage", agent=agent, target=path_label,
                     status="ERROR", detail=str(exc))
            return f"Error: {exc}"
        except RuntimeError as exc:
            log_call(sly_data, tool="OcrImage", agent=agent, target=path_label,
                     status="ERROR", detail=str(exc))
            logger.exception("OcrImage Claude API error for %s", path_label)
            return f"Error: {exc}"
        except Exception as exc:
            log_call(sly_data, tool="OcrImage", agent=agent, target=path_label,
                     status="ERROR", detail=str(exc))
            logger.exception("OcrImage unexpected error for %s", path_label)
            return f"Error: unexpected error reading image: {exc}"

        char_count = len(text)
        log_call(sly_data, tool="OcrImage", agent=agent, target=path_label,
                 status="OK", detail=f"model={model_key}  {char_count} chars extracted")
        logger.debug("OcrImage: %s â†’ %d chars  model=%s", path_label, char_count, model_key)
        return text

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        return await asyncio.to_thread(self.invoke, args, sly_data)

