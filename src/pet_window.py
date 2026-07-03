"""PetWindow: a transparent, borderless, always-on-top overlay window."""
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QBitmap, QMouseEvent, QPixmap
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from src.pet_renderer import PetRenderer
from src.state_machine import PetState


class PetWindow(QWidget):
    """A transparent window that floats above all others and displays the pet."""

    def __init__(self) -> None:
        super().__init__()

        # --- Window flags: frameless, always-on-top, no taskbar entry ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # --- Transparent background ---
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # --- Fixed size ---
        self.setFixedSize(128, 128)

        # --- Pet renderer (image display) ---
        self._renderer = PetRenderer(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._renderer.label)

        # --- Alpha-channel mask: only non-transparent pixels block clicks ---
        self._set_alpha_mask()

        # --- Center on screen ---
        self._center_on_screen()

        # --- Drag state ---
        self._dragging: bool = False
        self._drag_offset: QPoint = QPoint(0, 0)

        # --- Enable mouse tracking for move events ---
        self.setMouseTracking(True)

    # ------------------------------------------------------------------
    # Mask / hit-testing
    # ------------------------------------------------------------------

    def _set_alpha_mask(self) -> None:
        """Set a per-pixel mask from the pet image's alpha channel.

        Pixels with alpha > 0 block clicks; transparent pixels pass through.
        """
        pixmap: QPixmap = self._renderer.pixmap
        if pixmap.isNull():
            return

        # Scale pixmap to window size then extract alpha channel as mask
        scaled = pixmap.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        mask = scaled.createMaskFromColor(
            Qt.GlobalColor.transparent, Qt.MaskMode.MaskInColor
        )
        self.setMask(mask)

    # ------------------------------------------------------------------
    # Positioning
    # ------------------------------------------------------------------

    def _center_on_screen(self) -> None:
        """Position the window at the center of the primary screen."""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen is not None:
            center = screen.geometry().center()
            frame_geom = self.frameGeometry()
            frame_geom.moveCenter(center)
            self.move(frame_geom.topLeft())

    # ------------------------------------------------------------------
    # Drag
    # ------------------------------------------------------------------

    @property
    def is_dragging(self) -> bool:
        """True while the user is dragging the pet."""
        return self._dragging

    # ------------------------------------------------------------------
    # State visual
    # ------------------------------------------------------------------

    def set_pet_state(self, state: PetState) -> None:
        """Update the renderer's visual based on the current state."""
        self._renderer.set_state_visual(state)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start dragging the pet on left-click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            print(f"Pet drag start @ {self.pos().x()},{self.pos().y()}")

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Move the pet window while dragging."""
        if self._dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """End drag and release the pet."""
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            print(f"Pet drag end @ {self.pos().x()},{self.pos().y()}")

    def closeEvent(self, event) -> None:
        """Clean up when the window is closed."""
        print("PetWindow closed.")
        event.accept()
