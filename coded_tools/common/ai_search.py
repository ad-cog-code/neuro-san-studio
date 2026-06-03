"""
coded_tools/common/ai_search.py
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
AiSearch â€” search the web AND synthesise results into a focused answer.

Two-step process:
  1. Search DuckDuckGo for *query* (up to *max_results* hits).
  2. Call an LLM (via LiteLLM proxy â†’ fast chain / Haiku 4.5) to synthesise the raw
     snippets into a coherent, concise answer targeted to the *purpose*.

This is more useful than raw SearchWeb when the agent needs an answer,
not a list of links â€” e.g. "What is Cognizant's revenue for FY2025?"

Fallback behaviour:
  â€¢ If the LiteLLM proxy is unreachable â†’ returns formatted raw results.
  â€¢ If DuckDuckGo fails â†’ returns an error string.

HOCON class reference
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "class": "coded_tools.common.ai_search.AiSearch"

HOCON tool block (copy-paste into any network)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "name": "ai_search",
        "class": "coded_tools.common.ai_search.AiSearch",
        "function": {
            "description": "Search the web and synthesise results into a concise answer using AI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    },
                    "purpose": {
                        "type": "string",
                        "description": "What you need this information for â€” guides the AI synthesis. E.g. 'I am writing a bid for Acme Corp and need their recent financials.'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of web results to synthesise from (default: 8, max: 15)."
                    },
                    "timelimit": {
                        "type": "string",
                        "description": "Filter by time: 'd' (day), 'w' (week), 'm' (month). Omit for all time."
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

Environment / LiteLLM proxy
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    Reads LITELLM_PROXY_URL  (default: http://localhost:4000)
    Reads LITELLM_API_KEY    (default: sk-litellm-dev-key)
    Uses model: fast chain (Haiku 4.5 â€” fast + cheap for synthesis tasks)
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.common._base import log_call

logger = logging.getLogger(__name__)

MAX_ALLOWED_RESULTS = 15
DEFAULT_RESULTS     = 8

LITELLM_PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
LITELLM_API_KEY   = os.getenv("LITELLM_API_KEY",   "sk-litellm-dev-key")
SYNTHESIS_MODEL   = "fast"              # Haiku 4.5 via litellm-proxy; proxy falls back if needed

SYNTHESIS_SYSTEM = """\
You are a research assistant. You will be given:
  â€¢ A search query
  â€¢ The purpose for which the information is needed
  â€¢ A list of web search results (title + snippet + URL)

Your job is to synthesise the search results into a concise, factual answer
that directly serves the stated purpose. Use only information from the
provided search results â€” do not add facts from your training data.
Cite sources inline as [1], [2], etc., and list URLs at the end.
If the results don't contain enough information, say so clearly.
"""


def _format_results_plain(query: str, results: list[dict[str, str]]) -> str:
    """Format raw results when AI synthesis is unavailable."""
    lines = [f"Web search results for: {query!r}\n"]
    for i, hit in enumerate(results, 1):
        lines.append(f"{i}. {hit.get('title', '').strip()}")
        lines.append(f"   URL: {hit.get('href', '').strip()}")
        lines.append(f"   {hit.get('body', '').strip()}")
        lines.append("")
    return "\n".join(lines)


def _synthesise(query: str, purpose: str, results: list[dict[str, str]]) -> str:
    """Call LiteLLM proxy to synthesise search results. Returns None on failure."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=LITELLM_API_KEY, base_url=LITELLM_PROXY_URL)

        # Build the user message
        snippets = []
        for i, hit in enumerate(results, 1):
            snippets.append(
                f"[{i}] {hit.get('title', '')}\n"
                f"    URL: {hit.get('href', '')}\n"
                f"    {hit.get('body', '')}"
            )
        user_msg = (
            f"Search query: {query}\n\n"
            f"Purpose: {purpose or 'General research'}\n\n"
            f"Search results:\n\n" + "\n\n".join(snippets)
        )

        response = client.chat.completions.create(
            model=SYNTHESIS_MODEL,
            messages=[
                {"role": "system",  "content": SYNTHESIS_SYSTEM},
                {"role": "user",    "content": user_msg},
            ],
            max_tokens=1024,
            timeout=30,
        )
        return response.choices[0].message.content.strip()

    except Exception as exc:
        logger.warning("AiSearch synthesis failed (%s) â€” returning raw results", exc)
        return None


class AiSearch(CodedTool):
    """Search the web and synthesise results into a focused answer using AI."""

    def invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        from ddgs import DDGS

        query       = (args.get("query")   or "").strip()
        purpose     = (args.get("purpose") or "").strip()
        agent       = (args.get("agent")   or "unknown-agent").strip()
        max_results = min(int(args.get("max_results") or DEFAULT_RESULTS), MAX_ALLOWED_RESULTS)
        timelimit   =  args.get("timelimit")

        if not query:
            return "Error: ai_search requires 'query'."

        logger.debug("AiSearch: query=%r  purpose=%r  max=%d", query, purpose, max_results)

        # â”€â”€ Step 1: Web search â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        try:
            ddgs_params: dict[str, Any] = {"query": query, "max_results": max_results}
            if timelimit:
                ddgs_params["timelimit"] = timelimit
            raw_results: list[dict[str, str]] = DDGS().text(**ddgs_params)
        except Exception as exc:
            log_call(sly_data, tool="AiSearch", agent=agent, target=query,
                     status="ERROR", detail=f"search failed: {exc}")
            logger.exception("AiSearch web search failed: %s", query)
            return f"Error: web search failed: {exc}"

        if not raw_results:
            log_call(sly_data, tool="AiSearch", agent=agent, target=query,
                     status="OK", detail="0 results")
            return "No results found for your query. Try different search terms."

        # â”€â”€ Step 2: AI synthesis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        answer = _synthesise(query, purpose, raw_results)

        if answer:
            log_call(sly_data, tool="AiSearch", agent=agent, target=query,
                     status="OK", detail=f"synthesised from {len(raw_results)} results")
            logger.debug("AiSearch: synthesised answer (%d chars) from %d results",
                        len(answer), len(raw_results))
            return answer
        else:
            # Proxy unavailable â€” return plain formatted results
            log_call(sly_data, tool="AiSearch", agent=agent, target=query,
                     status="OK", detail=f"{len(raw_results)} results (no synthesis)")
            return _format_results_plain(query, raw_results)

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> str:
        return await asyncio.to_thread(self.invoke, args, sly_data)

