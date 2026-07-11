"""PetWindow: a transparent, borderless, always-on-top overlay window."""
import math
import random
from pathlib import Path

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBitmap, QFont, QMouseEvent, QPainter, QPixmap, QWheelEvent
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QVBoxLayout, QWidget,
)

from src.pet_renderer import PetRenderer
from src.state_machine import PetState


def _scaled_px(base_px: int, scale: float) -> int:
    """Scale a pixel value with a floor of 1 so nothing collapses to zero."""
    return max(1, round(base_px * scale))


class PetWindow(QWidget):
    """A transparent window that floats above all others and displays the pet."""

    BASE_SIZE = 128
    MIN_SIZE = 32
    MAX_SIZE = 512

    # Base values (at scale=1.0) — all derived sizes scale with the pet
    _BASE_BUTTON_AREA = 60
    _BASE_TOP_PADDING = 50

    # Minimum guard values so UI never collapses below usable thresholds
    _MIN_BUTTON_AREA = 36
    _MIN_TOP_PADDING = 20

    pet_image_changed = pyqtSignal(str)
    feed_requested = pyqtSignal()

    # ------------------------------------------------------------------
    # Dynamic padding (scale-aware)
    # ------------------------------------------------------------------

    @property
    def top_padding(self) -> int:
        s = self.scale
        return max(self._MIN_TOP_PADDING, round(self._BASE_TOP_PADDING * s))

    @property
    def button_area_height(self) -> int:
        s = self.scale
        return max(self._MIN_BUTTON_AREA, round(self._BASE_BUTTON_AREA * s))

    # ------------------------------------------------------------------

    def __init__(
        self, image_path: str | None = None, initial_size: int = BASE_SIZE,
    ) -> None:
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        if image_path is None:
            image_path = str(
                Path(__file__).resolve().parent / "assets" / "default_pet.png"
            )
        self._current_image_path = image_path

        self._size = initial_size
        self.setFixedSize(
            initial_size,
            self.top_padding + initial_size + self.button_area_height,
        )

        # --- Pet renderer ---
        self._renderer = PetRenderer(self, image_path=image_path, size=initial_size)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, self.top_padding, 0, 0)
        layout.addWidget(self._renderer.label)

        # --- Hunger bar ---
        hunger_layout = QHBoxLayout()
        hunger_layout.setContentsMargins(8, 4, 8, 4)

        self._hunger_icon = QLabel("🍖")
        self._hunger_icon.setFixedWidth(20)
        hunger_layout.addWidget(self._hunger_icon)

        self._hunger_bar = QProgressBar(self)
        self._hunger_bar.setRange(0, 100)
        self._hunger_bar.setValue(80)
        self._hunger_bar.setTextVisible(False)
        self._hunger_bar.setFixedHeight(10)
        self._hunger_bar.setStyleSheet("""
            QProgressBar {
                background-color: #E8E8E8;
                border: 1px solid #CCC;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF5252, stop:0.3 #FFC107, stop:0.7 #8BC34A, stop:1 #4CAF50
                );
                border-radius: 4px;
            }
        """)
        hunger_layout.addWidget(self._hunger_bar)
        layout.addLayout(hunger_layout)

        # --- Button row ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._interact_btn = QPushButton("🤚 互动")
        self._interact_btn.clicked.connect(self._on_interact_clicked)
        button_layout.addWidget(self._interact_btn)

        self._feed_btn = QPushButton("🥫 喂食")
        self._feed_btn.clicked.connect(self._on_feed_clicked)
        button_layout.addWidget(self._feed_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # --- Mask ---
        self._set_alpha_mask()
        self._renderer.frame_ready.connect(self._set_alpha_mask)

        # --- Position ---
        self._center_on_screen()

        # --- State ---
        self._dragging: bool = False
        self._drag_offset: QPoint = QPoint(0, 0)
        self._active_hearts: list = []
        self._is_foraging: bool = False

        # Hunger emoji timer — starts when hunger < 20
        self._hunger_timer = QTimer(self)
        self._hunger_timer.setInterval(2000)
        self._hunger_timer.timeout.connect(self._on_hunger_tick)

        self.setMouseTracking(True)
        self.setAcceptDrops(True)

        # Apply initial scale-aware styles
        self._apply_scale_styles()

    # ------------------------------------------------------------------
    # Mask
    # ------------------------------------------------------------------

    def _set_alpha_mask(self) -> None:
        pixmap: QPixmap = self._renderer.pixmap
        if pixmap.isNull():
            return

        tp = self.top_padding
        ba = self.button_area_height

        full_mask = QBitmap(self.size())
        full_mask.fill(Qt.GlobalColor.color0)

        painter = QPainter(full_mask)

        # Pet silhouette mask — only non-transparent pixels are visible
        scaled = pixmap.scaled(
            self._size, self._size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        pet_mask = scaled.createMaskFromColor(
            Qt.GlobalColor.transparent, Qt.MaskMode.MaskInColor
        )
        painter.drawPixmap(0, tp, pet_mask)

        # Button / status bar — always fully visible
        btn_top = self.height() - ba
        painter.fillRect(0, btn_top, self.width(), ba,
                         Qt.GlobalColor.color1)

        painter.end()
        self.setMask(full_mask)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_hunger(self, value: int) -> None:
        self._hunger_bar.setValue(value)
        # Auto-start / stop hunger emoji timer
        if value < 20:
            self._is_foraging = True
            if not self._hunger_timer.isActive():
                self._hunger_timer.start()
        else:
            self._is_foraging = False
            self._hunger_timer.stop()

    # ------------------------------------------------------------------
    # Particle effect (shared by hearts + hunger emojis)
    # ------------------------------------------------------------------

    def _spawn_particles(self, emojis: list[str], count: int) -> None:
        """Spawn *count* emoji particles that float outward from the pet image
        centre and fade to transparent.

        Each particle is an independent top-level tool window — not clipped
        by the shaped-window mask, click-through, and self-deleting.
        """
        s = self.scale

        # Centre of the pet image area (global screen coordinates)
        pet_cx = self.x() + self._size // 2
        pet_cy = self.y() + self.top_padding + self._size // 2

        for i in range(count):
            # --- Create label ---
            label = QLabel(random.choice(emojis))
            label.setWindowFlags(
                Qt.WindowType.Tool
                | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
            )
            label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

            font_size = _scaled_px(random.randint(16, 32), s)
            label.setFont(QFont("Segoe UI Emoji", font_size))
            label.adjustSize()

            # --- Position at pet centre ---
            label.move(pet_cx - label.width() // 2, pet_cy - label.height() // 2)

            # --- Opacity effect ---
            opacity_effect = QGraphicsOpacityEffect(label)
            opacity_effect.setOpacity(1.0)
            label.setGraphicsEffect(opacity_effect)

            # --- Random direction + distance ---
            angle = (2.0 * math.pi * i / count) + random.uniform(-0.3, 0.3)
            travel = _scaled_px(random.randint(40, 100), s)
            end_x = int(math.cos(angle) * travel)
            end_y = int(math.sin(angle) * travel)

            label.show()

            # --- Position animation ---
            pos_anim = QPropertyAnimation(label, b"pos", label)
            pos_anim.setEndValue(label.pos() + QPoint(end_x, end_y))
            pos_anim.setDuration(random.randint(800, 1200))
            pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            # --- Opacity animation ---
            op_anim = QPropertyAnimation(opacity_effect, b"opacity", label)
            op_anim.setEndValue(0.0)
            op_anim.setDuration(pos_anim.duration())
            op_anim.setEasingCurve(QEasingCurve.Type.InQuad)

            # --- Hold references + clean up on finish ---
            self._active_hearts.append((label, pos_anim, op_anim))
            op_anim.finished.connect(
                lambda lbl=label: self._cleanup_particle(lbl)
            )

            pos_anim.start()
            op_anim.start()

    def _cleanup_particle(self, label: QLabel) -> None:
        """Remove a particle label after its animation completes."""
        label.close()
        label.deleteLater()
        self._active_hearts = [
            t for t in self._active_hearts if t[0] is not label
        ]

    def _spawn_hearts(self) -> None:
        """Convenience wrapper — spawn heart particles for the 互动 button."""
        self._spawn_particles(
            ["❤️", "💕", "💗", "💖", "💝", "💘"], 10,
        )

    def _on_hunger_tick(self) -> None:
        """Called every 2 s while the pet is in foraging state (hunger < 20)."""
        self._spawn_particles(
            ["😫", "🥺", "😩", "😰", "💀", "🍞", "😿", "🥖"],
            random.randint(2, 3),
        )

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _on_interact_clicked(self) -> None:
        if self._is_foraging:
            return  # hungry pet ignores interaction
        self._spawn_hearts()

    def _on_feed_clicked(self) -> None:
        self.feed_pet()

    def feed_pet(self) -> None:
        self.feed_requested.emit()

    # ------------------------------------------------------------------
    # Positioning
    # ------------------------------------------------------------------

    def _center_on_screen(self) -> None:
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen is not None:
            center = screen.geometry().center()
            frame_geom = self.frameGeometry()
            frame_geom.moveCenter(center)
            self.move(frame_geom.topLeft())

    def set_position(self, x: int, y: int) -> None:
        self.move(x, y)

    def get_position(self) -> tuple[int, int]:
        return self.x(), self.y()

    @property
    def current_image_path(self) -> str:
        return self._current_image_path

    def set_image(self, image_path: str) -> None:
        self._current_image_path = image_path
        self._renderer.set_image(image_path)
        self._set_alpha_mask()

    # ------------------------------------------------------------------
    # Drag
    # ------------------------------------------------------------------

    @property
    def is_dragging(self) -> bool:
        return self._dragging

    # ------------------------------------------------------------------
    # State visual
    # ------------------------------------------------------------------

    def set_pet_state(self, state: PetState) -> None:
        self._renderer.set_state_visual(state)

    # ------------------------------------------------------------------
    # Size / scale
    # ------------------------------------------------------------------

    @property
    def scale(self) -> float:
        return self._size / self.BASE_SIZE

    def set_scale(self, scale: float) -> None:
        new_size = int(self.BASE_SIZE * scale)
        new_size = max(self.MIN_SIZE, min(self.MAX_SIZE, new_size))
        self._apply_resize(new_size)

    def _apply_resize(self, new_size: int) -> None:
        if new_size == self._size:
            return
        self._size = new_size
        tp = self.top_padding
        ba = self.button_area_height
        self.setFixedSize(new_size, tp + new_size + ba)
        # Update layout top margin for the new scale
        self.layout().setContentsMargins(0, tp, 0, 0)
        self._renderer.set_size(new_size, new_size)
        self._set_alpha_mask()
        self._apply_scale_styles()

    # ------------------------------------------------------------------
    # Scale-aware styling
    # ------------------------------------------------------------------

    def _apply_scale_styles(self) -> None:
        """Refresh button / control styles so font sizes track the pet scale."""
        s = self.scale
        btn_font = _scaled_px(12, s)
        self._interact_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: {btn_font}px;
                padding: 4px 10px;
            }}
        """)
        self._feed_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: {btn_font}px;
                padding: 4px 10px;
            }}
        """)

    # ------------------------------------------------------------------
    # Wheel event (resize)
    # ------------------------------------------------------------------

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        if delta > 0:
            new_size = int(self._size * 1.10)
        elif delta < 0:
            new_size = int(self._size * 0.90)
        else:
            return
        new_size = max(self.MIN_SIZE, min(self.MAX_SIZE, new_size))
        self._apply_resize(new_size)
        event.accept()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path_lower = url.toLocalFile().lower()
                    if path_lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                        event.acceptProposedAction()
                        return
        event.ignore()

    def dropEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                        self.set_image(file_path)
                        self.pet_image_changed.emit(file_path)
                        return

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.feed_requested.emit()
            event.accept()

    def closeEvent(self, event) -> None:
        event.accept()
