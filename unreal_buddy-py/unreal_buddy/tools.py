"""Tool definitions and execution for UnrealBuddy.

Two tools are available to Claude:

- ``fetch_url``: Fetches a URL and returns cleaned text. No API key needed.
  Best used with doc URLs already present in the KB.

- ``web_search``: Searches the web via Brave Search (proxied through the
  Cloudflare Worker). Requires ``BRAVE_API_KEY`` set as a Worker secret.
  Gracefully disabled if the key is not present.
"""

from __future__ import annotations

import asyncio
import logging
import re
from html.parser import HTMLParser

import httpx
from ddgs import DDGS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool definitions — passed to the Anthropic Messages API
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "fetch_url",
        "description": (
            "Fetch the text content of a specific URL and return it. "
            "Use this to read official Unreal Engine documentation pages, "
            "Epic Games blog posts, GitHub issues, or any specific webpage. "
            "Prefer this over web_search when you already know the exact URL "
            "(the knowledge base includes relevant documentation URLs)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to fetch (must start with http:// or https://).",
                }
            },
            "required": ["url"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Search the web via DuckDuckGo and return up to 5 results with titles, "
            "URLs, and descriptions. No API key required. "
            "Use this to find recent Unreal Engine announcements, community solutions "
            "on the Epic forums or AnswerHub, Stack Overflow answers, "
            "or any topic not covered in the knowledge base."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific for better results.",
                }
            },
            "required": ["query"],
        },
    },
]


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

async def execute_tool(name: str, input_data: dict, worker_url: str) -> str:
    """Execute a tool call and return its string output."""
    if name == "fetch_url":
        url = input_data.get("url", "")
        if not url:
            return "Error: url parameter is required."
        return await _fetch_url(url)

    if name == "web_search":
        query = input_data.get("query", "")
        if not query:
            return "Error: query parameter is required."
        return await _web_search(query, worker_url)

    return f"Unknown tool: {name!r}"


# ---------------------------------------------------------------------------
# fetch_url
# ---------------------------------------------------------------------------

class _HTMLTextExtractor(HTMLParser):
    """Minimal HTML-to-text extractor that skips scripts, styles, and nav."""

    _SKIP_TAGS = frozenset({"script", "style", "nav", "footer", "header", "noscript"})

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:  # noqa: ARG002
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self._parts.append(stripped)

    def get_text(self) -> str:
        # Collapse multiple blank lines
        raw = "\n".join(self._parts)
        return re.sub(r"\n{3,}", "\n\n", raw)


def _clean_html(html: str) -> str:
    extractor = _HTMLTextExtractor()
    try:
        extractor.feed(html)
    except Exception:  # noqa: BLE001
        return html  # fallback: return raw if parsing fails
    return extractor.get_text()


async def _fetch_url(url: str) -> str:
    """Fetch a URL and return cleaned plain text, truncated to 12 000 chars."""
    if not url.startswith(("http://", "https://")):
        return f"Error: invalid URL {url!r} — must start with http:// or https://"

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "UnrealBuddy/1.0 (documentation reader)",
                    "Accept": "text/html,application/xhtml+xml,text/plain",
                },
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "html" in content_type:
                text = _clean_html(response.text)
            else:
                text = response.text

            if len(text) > 12_000:
                text = text[:12_000] + "\n\n[content truncated at 12 000 characters]"

            return f"Content from {url}:\n\n{text}"

    except httpx.HTTPStatusError as exc:
        return f"HTTP {exc.response.status_code} fetching {url}"
    except httpx.TimeoutException:
        return f"Timeout fetching {url} (limit: 15 s)"
    except Exception as exc:  # noqa: BLE001
        logger.warning("fetch_url error for %s: %s", url, exc)
        return f"Error fetching {url}: {exc}"


# ---------------------------------------------------------------------------
# web_search  (proxied through the Cloudflare Worker)
# ---------------------------------------------------------------------------

def _ddg_search_sync(query: str) -> list[dict]:
    """Run a DuckDuckGo text search synchronously (called via asyncio.to_thread)."""
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=5))


async def _web_search(query: str, worker_url: str) -> str:  # noqa: ARG001
    """Search DuckDuckGo and return up to 5 results. No API key required."""
    try:
        hits = await asyncio.to_thread(_ddg_search_sync, query)

        if not hits:
            return f"No results found for: {query!r}"

        lines = [f"Search results for: {query}\n"]
        for i, r in enumerate(hits, 1):
            title = r.get("title", "No title")
            url = r.get("href", "")
            body = r.get("body", "").strip()
            lines.append(f"{i}. **{title}**")
            lines.append(f"   URL: {url}")
            if body:
                lines.append(f"   {body}")
            lines.append("")

        return "\n".join(lines)

    except Exception as exc:  # noqa: BLE001
        logger.warning("web_search error: %s", exc)
        return (
            f"Search failed ({exc}). "
            "Try fetch_url with a known documentation URL instead."
        )
