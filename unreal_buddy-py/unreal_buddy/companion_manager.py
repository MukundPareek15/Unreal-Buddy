"""CompanionManager — orchestration state machine for UnrealBuddy.

Text-input variant: the mic/transcription/TTS voice pipeline has been
replaced with a typed input workflow. Call ``submit_text(text)`` to kick
off a turn; the rest of the pipeline (screen capture → LLM → cursor
guidance) is unchanged.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from collections.abc import Callable
from typing import Any, Protocol

from PySide6.QtCore import QObject, Signal

from unreal_buddy.active_window import get_foreground_window_title
from unreal_buddy.clients.llm_client import LLMClient
from unreal_buddy.config import Config
from unreal_buddy.conversation_history import ConversationHistory
from unreal_buddy.knowledge_base import load_kb_from_disk, match_app, select_content
from unreal_buddy.point_mapper import map_point_to_screen
from unreal_buddy.point_parser import parse_point_tag
from unreal_buddy.prompts import build_system_prompt
from unreal_buddy.screen_capture import ScreenshotImage
from unreal_buddy.state import VoiceState

logger = logging.getLogger(__name__)


class CaptureVisibilityController(Protocol):
    """Protocol for hiding/restoring UI during screen capture."""

    def hide_for_capture(self) -> None: ...
    def restore_after_capture(self) -> None: ...
    def fly_to(self, x: int, y: int) -> None: ...


class CompanionManager(QObject):
    """Orchestration state machine for the text-input companion pipeline.

    Call ``submit_text(text)`` to start a turn. Emits Qt signals that the
    UI layer binds to — no knowledge of which widgets are connected.
    """

    # ---- Qt signals ----
    state_changed = Signal(VoiceState)
    final_transcript = Signal(str)      # user's submitted query (for history)
    response_delta = Signal(str)        # streaming LLM token
    response_complete = Signal(str)     # full response text when done
    success_turn_completed = Signal()
    error = Signal(str)

    def __init__(
        self,
        config: Config,
        llm: LLMClient,
        screen_capture_fn: Callable[[], list[ScreenshotImage]],
        panel_visibility_controller: CaptureVisibilityController,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._config = config
        self._llm = llm
        self._screen_capture_fn = screen_capture_fn
        self._panel_visibility_controller = panel_visibility_controller

        self._state: VoiceState = VoiceState.IDLE
        self._current_task: asyncio.Task[None] | None = None
        self._history = ConversationHistory()
        self._knowledge_dir = config.knowledge_dir
        self._current_model: str = config.default_model
        self._cancel_flag: bool = False
        self._current_screenshots: list[ScreenshotImage] = []

        self._llm.delta.connect(self._on_llm_delta)
        self._llm.error.connect(self._on_error)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_model(self, model_id: str) -> None:
        """Switch the Claude model used for subsequent requests."""
        self._current_model = model_id

    def submit_text(self, text: str) -> None:
        """Submit a typed query. Cancels any in-flight turn first."""
        text = text.strip()
        if not text:
            return

        # Cancel any running turn so the new one starts clean.
        if self._state != VoiceState.IDLE:
            self._cancel_flag = True
        if self._current_task is not None and not self._current_task.done():
            self._current_task.cancel()

        self._cancel_flag = False
        self._current_task = asyncio.ensure_future(self._run_turn(text))

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def _set_state(self, new_state: VoiceState) -> None:
        self._state = new_state
        self.state_changed.emit(new_state)

    # ------------------------------------------------------------------
    # LLM delta relay
    # ------------------------------------------------------------------

    def _on_llm_delta(self, text: str) -> None:
        if not self._cancel_flag:
            self.response_delta.emit(text)

    # ------------------------------------------------------------------
    # Error handler
    # ------------------------------------------------------------------

    def _on_error(self, msg: str) -> None:
        logger.error("companion error: %s", msg)
        self.error.emit(msg)
        self._set_state(VoiceState.IDLE)

    # ------------------------------------------------------------------
    # Turn pipeline
    # ------------------------------------------------------------------

    async def _run_turn(self, text: str) -> None:
        """Execute one full turn: screen capture → LLM → cursor guidance."""
        try:
            # Yield so any pending Qt events settle before we capture.
            await asyncio.sleep(0)

            self.final_transcript.emit(text)

            # Hide overlay so it doesn't appear in the screenshot.
            self._panel_visibility_controller.hide_for_capture()
            await asyncio.sleep(0.05)
            try:
                screenshots = await asyncio.to_thread(self._screen_capture_fn)
                self._current_screenshots = screenshots
            finally:
                self._panel_visibility_controller.restore_after_capture()

            # Build image content blocks for the messages API.
            image_blocks: list[dict[str, Any]] = []
            for screenshot in screenshots:
                b64 = base64.b64encode(screenshot.jpeg_bytes).decode("ascii")
                image_blocks.append({"type": "text", "text": screenshot.label})
                image_blocks.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64,
                        },
                    }
                )

            messages = self._history.messages_for_request(
                current_user_text=text,
                current_images=image_blocks,
            )

            # Detect active app and load matching KB.
            window_title = get_foreground_window_title()
            kb_content = None
            app_name = None
            if self._knowledge_dir is not None:
                apps = load_kb_from_disk(self._knowledge_dir)
                matched = match_app(window_title, apps)
                if matched is not None:
                    app_name = matched.name
                    kb_content = select_content(matched, text)
                    logger.info("KB loaded: %s (%d chars)", app_name, len(kb_content))
                else:
                    logger.debug("no KB match for window: %s", window_title)

            system_prompt = build_system_prompt(kb_content, app_name)

            self._set_state(VoiceState.PROCESSING)

            full_text = await self._llm.send(
                messages,
                system=system_prompt,
                model=self._current_model,
            )

            if not self._cancel_flag:
                self._history.append(text, full_text)
                self.response_complete.emit(full_text)
                self.success_turn_completed.emit()

                # Parse POINT tag — strip from displayed text, fly cursor if found.
                _display_text, point_tag = parse_point_tag(full_text)
                if point_tag is not None:
                    coords = map_point_to_screen(point_tag, self._current_screenshots)
                    if coords is not None:
                        self._panel_visibility_controller.fly_to(coords[0], coords[1])
                        logger.info(
                            "POINT: (%d, %d) label=%s",
                            coords[0], coords[1], point_tag.label,
                        )

            self._set_state(VoiceState.IDLE)

        except asyncio.CancelledError:
            logger.debug("turn cancelled")
            self._set_state(VoiceState.IDLE)

        except Exception as exc:  # noqa: BLE001
            logger.error("turn pipeline error: %s", exc)
            self.error.emit(str(exc))
            self._set_state(VoiceState.IDLE)
