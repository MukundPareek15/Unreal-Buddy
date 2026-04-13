"""Anthropic SSE stream parser and streaming HTTP client with tool-use support.

Two layers:

1. ``parse_anthropic_sse_stream`` — pure bytes-to-text-delta parser.
   Zero Qt / async / network dependencies. Kept intact for unit tests.

2. ``LLMClient`` — QObject that runs an agentic tool-use loop:
   stream → detect tool calls → execute → stream again → … → final answer.
   Emits ``delta`` signals for every text fragment so the UI streams live.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Iterator

import httpx
from PySide6.QtCore import QObject, Signal

from unreal_buddy.tools import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)

# Maximum tool-call roundtrips per turn (guards against infinite loops)
_MAX_TOOL_TURNS = 5


# ---------------------------------------------------------------------------
# Original pure SSE parser — kept for unit tests
# ---------------------------------------------------------------------------

def parse_anthropic_sse_stream(raw: bytes) -> Iterator[str]:
    """Parse an Anthropic SSE byte stream and yield text delta strings.

    Splits the raw bytes on double-newline SSE event boundaries, extracts
    ``event:`` and ``data:`` fields, and yields the ``text`` value from
    ``content_block_delta`` events whose delta type is ``text_delta``.

    Unknown ``content_block_start`` types are silently skipped — any subsequent
    ``content_block_delta`` events for that block are also skipped, preventing
    crashes when the API introduces new block types.

    Events ``message_start``, ``message_delta``, ``message_stop``,
    ``content_block_stop``, and ``ping`` are ignored.
    """
    if not raw:
        return

    # Normalise Windows (\r\n) and classic Mac (\r) line endings so the
    # double-newline SSE boundary split works regardless of source platform.
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    chunks = text.split("\n\n")

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        event_type: str | None = None
        data_line: str | None = None

        for line in chunk.splitlines():
            if line.startswith("event:"):
                event_type = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data_line = line[len("data:"):].strip()

        if event_type is None or data_line is None:
            continue
        if event_type != "content_block_delta":
            continue

        try:
            payload = json.loads(data_line)
        except json.JSONDecodeError:
            continue

        delta = payload.get("delta", {})
        if delta.get("type") == "text_delta":
            text_fragment = delta.get("text", "")
            if text_fragment:
                yield text_fragment


# ---------------------------------------------------------------------------
# Internal dataclasses for the tool-use loop
# ---------------------------------------------------------------------------

@dataclass
class _ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class _TurnResult:
    """Result of one streaming LLM call."""
    text: str                              # text produced this turn
    stop_reason: str                       # "end_turn" | "tool_use"
    tool_calls: list[_ToolCall] = field(default_factory=list)
    content_blocks: list[dict] = field(default_factory=list)  # for message history


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------

class LLMClient(QObject):
    """Streaming Anthropic client with agentic tool-use loop.

    Signals:
        delta(str):  Text fragment arriving live from the stream.
        done(str):   Full accumulated response text when the turn is complete.
        error(str):  Any exception that aborted the request.
    """

    delta = Signal(str)
    done = Signal(str)
    error = Signal(str)

    def __init__(self, worker_url: str, *, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._worker_url = worker_url.rstrip("/")

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def send(
        self,
        messages: list[dict],
        system: str,
        model: str,
        max_tokens: int = 2048,
    ) -> str:
        """Run the full agentic loop and return the complete response text.

        If Claude calls tools, they are executed and results fed back until
        Claude produces a final ``end_turn`` response. Tool activity is
        emitted as delta fragments so the UI stays live throughout.

        Returns:
            Fully accumulated response text across all turns.
        """
        working_messages = list(messages)
        full_text = ""

        try:
            for _turn in range(_MAX_TOOL_TURNS):
                result = await self._stream_turn(
                    working_messages, system, model, max_tokens
                )
                full_text += result.text

                # No tool calls — we have the final answer
                if result.stop_reason != "tool_use" or not result.tool_calls:
                    break

                # Execute each tool and append results to the conversation
                tool_results: list[dict] = []
                for tc in result.tool_calls:
                    status = self._tool_status_line(tc)
                    self.delta.emit(status)
                    full_text += status

                    logger.info("tool call: %s(%s)", tc.name, tc.input)
                    output = await execute_tool(tc.name, tc.input, self._worker_url)
                    logger.debug("tool result (%s): %s chars", tc.name, len(output))

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": output,
                    })

                working_messages = [
                    *working_messages,
                    {"role": "assistant", "content": result.content_blocks},
                    {"role": "user", "content": tool_results},
                ]

            self.done.emit(full_text)
            return full_text

        except asyncio.CancelledError:
            logger.debug("LLMClient.send() cancelled")
            raise

        except Exception as exc:
            self.error.emit(str(exc))
            raise

    # ------------------------------------------------------------------
    # Private: single streaming turn
    # ------------------------------------------------------------------

    async def _stream_turn(
        self,
        messages: list[dict],
        system: str,
        model: str,
        max_tokens: int,
    ) -> _TurnResult:
        """Stream one LLM request and return a structured result.

        Accumulates both text deltas (emitting each via ``delta``) and
        tool-use input JSON so the caller can execute any tool calls.
        """
        url = f"{self._worker_url}/chat"
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "stream": True,
            "system": system,
            "messages": messages,
            "tools": TOOL_DEFINITIONS,
        }

        # Per-block tracking
        blocks: dict[int, dict] = {}          # index → content_block_start payload
        text_parts: dict[int, list[str]] = {}  # index → text fragments
        json_parts: dict[int, list[str]] = {}  # index → input_json fragments
        stop_reason = "end_turn"
        buf = b""

        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream("POST", url, json=body) as response:
                response.raise_for_status()

                async for chunk in response.aiter_bytes():
                    buf += chunk

                    while b"\n\n" in buf:
                        raw_event, buf = buf.split(b"\n\n", 1)
                        event_type, data = _parse_sse_event(raw_event + b"\n\n")
                        if event_type is None or data is None:
                            continue

                        if event_type == "content_block_start":
                            idx = data.get("index", 0)
                            cb = data.get("content_block", {})
                            blocks[idx] = cb
                            if cb.get("type") == "text":
                                text_parts[idx] = [cb.get("text", "")]
                            elif cb.get("type") == "tool_use":
                                json_parts[idx] = []

                        elif event_type == "content_block_delta":
                            idx = data.get("index", 0)
                            delta = data.get("delta", {})
                            dtype = delta.get("type")

                            if dtype == "text_delta":
                                frag = delta.get("text", "")
                                if frag:
                                    text_parts.setdefault(idx, []).append(frag)
                                    self.delta.emit(frag)

                            elif dtype == "input_json_delta":
                                partial = delta.get("partial_json", "")
                                json_parts.setdefault(idx, []).append(partial)

                        elif event_type == "message_delta":
                            stop_reason = (
                                data.get("delta", {}).get("stop_reason") or "end_turn"
                            )

        # Flush any trailing buffer bytes
        if buf.strip():
            event_type, data = _parse_sse_event(buf)
            if event_type == "content_block_delta" and data:
                idx = data.get("index", 0)
                delta_obj = data.get("delta", {})
                if delta_obj.get("type") == "text_delta":
                    frag = delta_obj.get("text", "")
                    if frag:
                        text_parts.setdefault(idx, []).append(frag)
                        self.delta.emit(frag)

        # Assemble the turn result
        turn_text = ""
        tool_calls: list[_ToolCall] = []
        content_blocks: list[dict] = []

        for idx in sorted(blocks):
            cb = blocks[idx]
            cb_type = cb.get("type")

            if cb_type == "text":
                text = "".join(text_parts.get(idx, []))
                turn_text += text
                if text:
                    content_blocks.append({"type": "text", "text": text})

            elif cb_type == "tool_use":
                raw_json = "".join(json_parts.get(idx, []))
                try:
                    input_dict = json.loads(raw_json) if raw_json else {}
                except json.JSONDecodeError:
                    logger.warning("could not parse tool input JSON: %r", raw_json)
                    input_dict = {}

                tool_calls.append(_ToolCall(
                    id=cb.get("id", ""),
                    name=cb.get("name", ""),
                    input=input_dict,
                ))
                content_blocks.append({
                    "type": "tool_use",
                    "id": cb.get("id", ""),
                    "name": cb.get("name", ""),
                    "input": input_dict,
                })

        return _TurnResult(
            text=turn_text,
            stop_reason=stop_reason,
            tool_calls=tool_calls,
            content_blocks=content_blocks,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tool_status_line(tc: _ToolCall) -> str:
        if tc.name == "fetch_url":
            url = tc.input.get("url", "")
            return f"\n\n[fetching: {url}]\n\n"
        if tc.name == "web_search":
            query = tc.input.get("query", "")
            return f"\n\n[searching: {query}]\n\n"
        return f"\n\n[calling tool: {tc.name}]\n\n"


# ---------------------------------------------------------------------------
# SSE event parser helper
# ---------------------------------------------------------------------------

def _parse_sse_event(raw: bytes) -> tuple[str | None, dict | None]:
    """Parse one SSE event block into (event_type, data_dict).

    Returns (None, None) if the block is malformed or has no data.
    """
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    event_type: str | None = None
    data_line: str | None = None

    for line in text.splitlines():
        if line.startswith("event:"):
            event_type = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data_line = line[len("data:"):].strip()

    if event_type is None or data_line is None:
        return None, None

    try:
        return event_type, json.loads(data_line)
    except json.JSONDecodeError:
        return event_type, None
