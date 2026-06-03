"""
coded_tools/common/search_web.py
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
SearchWeb â€” search the web using DuckDuckGo and return structured results.

Returns up to *max_results* hits, each containing:
    title   â€” page title
    url     â€” page URL
    snippet â€” short description / excerpt

No API key required. Calls DuckDuckGo via the `ddgs` package.

HOCON class reference
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "class": "coded_tools.common.search_web.SearchWeb"

HOCON tool block (copy-paste into any network)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "name": "search_web",
        "class": "coded_tools.common.search_web.SearchWeb",
        "function": {
            "description": "Search the web using DuckDuckGo. Returns titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5, max: 20)."
                    },
                    "region": {
                        "type": "string",
                        "description": "Region code for localised results, e.g. 'in-en' for India, 'us-en' for US. Default: 'wt-wt' (worldwide)."
                    },
                    "timelimit": {
                        "type": "string",
                        "description": "Filter by time: 'd' (day), 'w' (week), 'm' (month), 'y' (year). Omit for all time."
                    },
                    "agent": {
                        "type": "string",
                        "description": "Name of the calling agent (used in audit log)."
                    }
                },
                "required": ["query"]
            }
        }
    }

sly_data keys read
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    None required. workspace_dir used only for audit logging.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.common._base import log_call

logger = logging.getLogger(__name__)

MAX_ALLOWED_RESULTS = 20
DEFAULT_RESULTS     = 5


class SearchWeb(CodedTool):
    """Search the web with DuckDuckGo. Returns structured results."""

    def invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        from ddgs import DDGS

        query       = (args.get("query") or "").strip()
        agent       = (args.get("agent") or "unknown-agent").strip()
        max_results = min(int(args.get("max_results") or DEFAULT_RESULTS), MAX_ALLOWED_RESULTS)
        region      = (args.get("region")    or "wt-wt").strip()
        timelimit   =  args.get("timelimit")  # optional â€” None means no filter

        if not query:
            return "Error: search_web requires 'query'."

        logger.debug("SearchWeb: query=%r  max=%d  region=%s", query, max_results, region)

        try:
            ddgs_params: dict[str, Any] = {
                "query":       query,
                "region":      region,
                "max_results": max_results,
            }
            if timelimit:
                ddgs_params["timelimit"] = timelimit

            raw_results: list[dict[str, str]] = DDGS().text(**ddgs_params)
        except Exception as exc:
            log_call(sly_data, tool="SearchWeb", agent=agent, target=query,
                     status="ERROR", detail=str(exc))
            logger.exception("SearchWeb failed for query: %s", query)
            return f"Error: web search failed: {exc}"

        if not raw_results:
            log_call(sly_data, tool="SearchWeb", agent=agent, target=query,
                     status="OK", detail="0 results")
            return "No results found for your query. Try different search terms."

        # Format results as numbered list for easy agent consumption
        lines = [f"Web search results for: {query!r}\n"]
        for i, hit in enumerate(raw_results, 1):
            title   = hit.get("title",   "").strip()
            url     = hit.get("href",    "").strip()
            snippet = hit.get("body",    "").strip()
            lines.append(f"{i}. {title}")
            lines.append(f"   URL: {url}")
            lines.append(f"   {snippet}")
            lines.append("")

        log_call(sly_data, tool="SearchWeb", agent=agent, target=query,
                 status="OK", detail=f"{len(raw_results)} results")
        logger.debug("SearchWeb: %d results for %r", len(raw_results), query)
        return "\n".join(lines)

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        return await asyncio.to_thread(self.invoke, args, sly_data)

