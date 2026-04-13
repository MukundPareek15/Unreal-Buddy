"""Floating text input panel for UnrealBuddy.

A frameless, always-on-top overlay with a text field and streaming response
area. Replaces the push-to-talk voice pipeline with a typed input workflow.

Hotkey (Ctrl+Alt) focuses the input field. Enter submits. Escape clears.
The widget is draggable by clicking anywhere except the input field.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from unreal_buddy.design_system import DS
from unreal_buddy.state import VoiceState


class TextInputWidget(QWidget):
    """Floating text input panel that submits queries to CompanionManager."""

    submitted = Signal(str)

    WIDTH = 420
    RESPONSE_MAX_H = 160

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(self.WIDTH)

        self._drag_pos = None
        self._build_ui()
        self._position_default()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Outer container — rounded dark card
        self._card = QFrame(self)
        self._card.setObjectName("card")
        self._card.setStyleSheet(f"""
            QFrame#card {{
                background-color: {DS.Colors.panel_bg};
                border-radius: {DS.CornerRadius.large}px;
                border: 1px solid {DS.Colors.border};
            }}
        """)
        outer.addWidget(self._card)

        inner = QVBoxLayout(self._card)
        inner.setContentsMargins(
            DS.Spacing.md, DS.Spacing.sm, DS.Spacing.md, DS.Spacing.md
        )
        inner.setSpacing(DS.Spacing.sm)

        # ── Header row ──────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(DS.Spacing.xs)

        self._dot = QLabel("●")
        self._dot.setFixedWidth(14)
        self._dot.setStyleSheet(
            f"color: {DS.Colors.companion_idle}; font-size: 10px; background: transparent;"
        )

        self._status = QLabel("buddy")
        self._status.setStyleSheet(
            f"color: {DS.Colors.text_secondary}; "
            f"font-size: {DS.Fonts.size_sm}px; background: transparent;"
        )

        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                color: {DS.Colors.text_secondary};
                background: transparent;
                border: none;
                font-size: 18px;
                padding: 0;
                line-height: 1;
            }}
            QPushButton:hover {{ color: {DS.Colors.text_primary}; }}
        """)
        close_btn.clicked.connect(self.hide)

        header.addWidget(self._dot)
        header.addWidget(self._status)
        header.addStretch()
        header.addWidget(close_btn)
        inner.addLayout(header)

        # ── Response area (hidden until response arrives) ────
        self._response = QTextEdit()
        self._response.setReadOnly(True)
        self._response.setFrameShape(QTextEdit.Shape.NoFrame)
        self._response.setMaximumHeight(self.RESPONSE_MAX_H)
        self._response.setMinimumHeight(0)
        self._response.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._response.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: {DS.Colors.text_primary};
                font-size: {DS.Fonts.size_md}px;
                border: none;
                padding: 0;
            }}
            QScrollBar:vertical {{
                width: 4px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {DS.Colors.border};
                border-radius: 2px;
            }}
        """)
        self._response.hide()
        inner.addWidget(self._response)

        # ── Input row ────────────────────────────────────────
        input_row = QHBoxLayout()
        input_row.setSpacing(DS.Spacing.sm)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Ask about your screen…")
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {DS.Colors.surface};
                color: {DS.Colors.text_primary};
                border: 1px solid {DS.Colors.border};
                border-radius: {DS.CornerRadius.small}px;
                padding: 7px {DS.Spacing.sm}px;
                font-size: {DS.Fonts.size_md}px;
            }}
            QLineEdit:focus {{
                border-color: {DS.Colors.accent_blue};
                outline: none;
            }}
            QLineEdit:disabled {{
                color: {DS.Colors.text_secondary};
            }}
        """)
        self._input.returnPressed.connect(self._on_submit)

        self._send_btn = QPushButton("↵")
        self._send_btn.setFixedSize(36, 36)
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.setToolTip("Send (Enter)")
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DS.Colors.accent_blue};
                color: white;
                border: none;
                border-radius: {DS.CornerRadius.small}px;
                font-size: 16px;
            }}
            QPushButton:hover {{ background-color: #6ab3ff; }}
            QPushButton:pressed {{ background-color: #2e7dd6; }}
            QPushButton:disabled {{
                background-color: {DS.Colors.border};
                color: {DS.Colors.text_secondary};
            }}
        """)
        self._send_btn.clicked.connect(self._on_submit)

        input_row.addWidget(self._input)
        input_row.addWidget(self._send_btn)
        inner.addLayout(input_row)

    def _position_default(self) -> None:
        """Place at bottom-center of primary screen, above the taskbar."""
        screen = QApplication.primaryScreen()
        if screen is None:
            self.move(100, 100)
            return
        self.adjustSize()
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - self.WIDTH) // 2
        y = geo.y() + geo.height() - self.height() - 60
        self.move(x, y)

    # ------------------------------------------------------------------
    # Drag support — entire widget except the input field is a drag handle
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    # ------------------------------------------------------------------
    # Public slots — called by app.py signal wiring
    # ------------------------------------------------------------------

    @Slot()
    def toggle_focus(self) -> None:
        """Called by the hotkey — show the panel and focus the input field."""
        if not self.isVisible():
            self.show()
        self.activateWindow()
        self.raise_()
        self._input.setFocus()

    @Slot()
    def clear_input(self) -> None:
        """Called by Escape — clear the input field."""
        self._input.clear()

    @Slot(object)
    def set_state(self, state: VoiceState) -> None:
        state_colors = {
            VoiceState.IDLE: DS.Colors.companion_idle,
            VoiceState.PROCESSING: DS.Colors.companion_processing,
            VoiceState.RESPONDING: DS.Colors.companion_responding,
        }
        state_labels = {
            VoiceState.IDLE: "buddy",
            VoiceState.PROCESSING: "thinking…",
            VoiceState.RESPONDING: "responding",
        }
        color = state_colors.get(state, DS.Colors.companion_idle)
        self._dot.setStyleSheet(
            f"color: {color}; font-size: 10px; background: transparent;"
        )
        self._status.setText(state_labels.get(state, "buddy"))

        busy = state in (VoiceState.PROCESSING, VoiceState.RESPONDING)
        self._input.setEnabled(not busy)
        self._send_btn.setEnabled(not busy)

    @Slot(str)
    def append_delta(self, text: str) -> None:
        """Stream Claude's response text into the response area."""
        if not self._response.isVisible():
            self._response.show()
            self.adjustSize()
        self._response.moveCursor(QTextCursor.MoveOperation.End)
        self._response.insertPlainText(text)
        sb = self._response.verticalScrollBar()
        sb.setValue(sb.maximum())

    @Slot(str)
    def commit_turn(self, _text: str = "") -> None:
        """Called when the full response has arrived — nothing extra needed."""
        pass

    @Slot(str)
    def show_error(self, msg: str) -> None:
        if not self._response.isVisible():
            self._response.show()
            self.adjustSize()
        cursor = self._response.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(DS.Colors.error_red))
        cursor.insertText(f"Error: {msg}", fmt)
        self._response.setTextCursor(cursor)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_submit(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        # Clear previous response so the new one streams in fresh
        self._response.clear()
        self._response.hide()
        self.adjustSize()
        self.submitted.emit(text)
