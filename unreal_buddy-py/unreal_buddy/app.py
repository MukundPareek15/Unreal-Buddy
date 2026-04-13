"""UnrealBuddy QApplication bootstrap — text-input variant.

Voice pipeline (mic / AssemblyAI / ElevenLabs) has been replaced with a
floating text input panel. Only an Anthropic API key (via the Cloudflare
Worker) is required.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from dataclasses import dataclass
from pathlib import Path

import qasync
from platformdirs import user_config_dir, user_log_dir
from PySide6.QtWidgets import QApplication

from unreal_buddy.clients.llm_client import LLMClient
from unreal_buddy.companion_manager import CompanionManager
from unreal_buddy.config import Config, ConfigError
from unreal_buddy.hotkey import HotkeyMonitor
from unreal_buddy.logging_config import configure_logging
from unreal_buddy.screen_capture import capture_all
from unreal_buddy.state import VoiceState
from unreal_buddy.ui.companion_widget import CompanionWidget
from unreal_buddy.ui.history_window import HistoryWindow
from unreal_buddy.ui.text_input_widget import TextInputWidget
from unreal_buddy.ui.tray_icon import TrayIcon

APP_NAME = "UnrealBuddy"
APP_AUTHOR = "UnrealBuddy"

logger = logging.getLogger(__name__)


@dataclass
class BootstrapResult:
    app: QApplication
    config: Config | None
    config_error: ConfigError | None
    was_first_run: bool
    config_path: Path
    log_dir: Path


def _example_config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "config.example.toml"


def bootstrap(argv: list[str] | None = None) -> BootstrapResult:
    argv = argv if argv is not None else sys.argv
    app = QApplication(argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_AUTHOR)
    app.setQuitOnLastWindowClosed(False)

    config_dir = Path(user_config_dir(APP_NAME, appauthor=False, roaming=True))
    config_path = config_dir / "config.toml"
    log_dir = Path(user_log_dir(APP_NAME, appauthor=False))

    was_first_run = Config.ensure_exists(config_path, _example_config_path())

    try:
        config = Config.from_path(config_path)
        config_error = None
    except ConfigError as exc:
        config = None
        config_error = exc

    return BootstrapResult(
        app=app,
        config=config,
        config_error=config_error,
        was_first_run=was_first_run,
        config_path=config_path,
        log_dir=log_dir,
    )


def run() -> int:
    """Start the UnrealBuddy tray app and run the Qt event loop."""
    result = bootstrap()

    log_level = result.config.log_level if result.config else "INFO"
    configure_logging(result.log_dir, log_level)

    if result.was_first_run:
        logger.info("first run: created config at %s", result.config_path)

    if result.config_error is not None:
        logger.warning("config error: %s", result.config_error)

    # ── Persistent UI components ─────────────────────────────────────
    tray_icon = TrayIcon()
    companion = CompanionWidget()      # cursor-following triangle overlay
    text_input = TextInputWidget()     # floating typed-query panel
    history = HistoryWindow()

    # Tray menu → settings / history
    tray_icon.show_settings_requested.connect(
        lambda: os.startfile(result.config_path)
    )
    tray_icon.show_history_requested.connect(history.show)
    tray_icon.show_history_requested.connect(history.raise_)

    # ── Hotkey monitor ───────────────────────────────────────────────
    hotkey_binding = result.config.hotkey if result.config is not None else "ctrl+alt"
    hotkey_monitor = HotkeyMonitor(binding=hotkey_binding)

    # Hotkey focuses the text input panel; Escape clears the input field.
    hotkey_monitor.pressed.connect(text_input.toggle_focus)
    hotkey_monitor.escape_pressed.connect(text_input.clear_input)

    # ── CompanionManager (only when config loaded successfully) ───────
    if result.config is not None:
        llm = LLMClient(worker_url=result.config.worker_url)
        manager = CompanionManager(
            config=result.config,
            llm=llm,
            screen_capture_fn=capture_all,
            panel_visibility_controller=companion,
        )

        # Text input → manager
        text_input.submitted.connect(manager.submit_text)

        # Manager state → companion triangle + text input indicator
        manager.state_changed.connect(companion.set_state)
        manager.state_changed.connect(text_input.set_state)

        # Streaming response → text input panel
        manager.response_delta.connect(text_input.append_delta)
        manager.response_complete.connect(text_input.commit_turn)

        # Errors → companion flash + text input panel + log
        manager.error.connect(lambda msg: logger.error("error: %s", msg))
        manager.error.connect(companion.flash_error)
        manager.error.connect(text_input.show_error)

        # Transcript + response → history window
        manager.final_transcript.connect(history.set_final)
        manager.response_delta.connect(history.append_delta)
        manager.response_complete.connect(history.commit_turn)
        manager.error.connect(history.show_error)

        # Log completions
        manager.response_complete.connect(
            lambda text: logger.info("response complete: %s", text[:120])
        )

    hotkey_monitor.start()
    tray_icon.show()
    companion.show()
    text_input.show()

    result.app.aboutToQuit.connect(hotkey_monitor.stop)
    result.app.aboutToQuit.connect(companion.hide)

    loop = qasync.QEventLoop(result.app)
    asyncio.set_event_loop(loop)
    signal.signal(signal.SIGINT, lambda *_: result.app.quit())

    with loop:
        loop.run_forever()
    return 0
