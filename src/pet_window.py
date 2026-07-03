"""PetWindow: a transparent, borderless, always-on-top overlay window."""
from pathlib import Path

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QBitmap, QMouseEvent, QPixmap, QWheelEvent
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from src.pet_renderer import PetRenderer
from src.state_machine import PetState


class PetWindow(QWidget):
    """A transparent window that floats above all others and displays the pet."""

    # The reference size at scale = 1.0
    BASE_SIZE = 128
    MIN_SIZE = 32
    MAX_SIZE = 512

    # Emitted when the user drops a new image onto the pet window
    pet_image_changed = pyqtSignal(str)

    # Emitted when the user double-clicks the pet (→ feed)
    feed_requested = pyqtSignal()

    def __init__(
        self, image_path: str | None = None, initial_size: int = BASE_SIZE,
    ) -> None:
        super().__init__()

        # --- Window flags: frameless, always-on-top, no taskbar entry ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # --- Transparent background ---
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # --- Resolve default pet path (same logic as PetRenderer's fallback) ---
        if image_path is None:
            image_path = str(
                Path(__file__).resolve().parent / "assets" / "default_pet.png"
            )
        self._current_image_path = image_path

        # --- Fixed size ---
        self._size = initial_size
        self.setFixedSize(initial_size, initial_size)

        # --- Pet renderer (image display) ---
        self._renderer = PetRenderer(
            self, image_path=image_path, size=initial_size,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._renderer.label)

        # --- Alpha-channel mask: only non-transparent pixels block clicks ---
        self._set_alpha_mask()

        # --- Position: center on screen (caller may override via set_position) ---
        self._center_on_screen()

        # --- Drag state ---
        self._dragging: bool = False
        self._drag_offset: QPoint = QPoint(0, 0)

        # --- Enable mouse tracking for move events ---
        self.setMouseTracking(True)

        # --- Accept drag & drop of image files ---
        self.setAcceptDrops(True)

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

    def set_position(self, x: int, y: int) -> None:
        """Move the window to the given screen coordinates."""
        self.move(x, y)

    def get_position(self) -> tuple[int, int]:
        """Return the window's current top-left (x, y) in screen coordinates."""
        return self.x(), self.y()

    @property
    def current_image_path(self) -> str:
        """Path to the currently displayed pet image file."""
        return self._current_image_path

    def set_image(self, image_path: str) -> None:
        """Replace the pet image and refresh the click-through mask."""
        self._current_image_path = image_path
        self._renderer.set_image(image_path)
        self._set_alpha_mask()

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
    # Size / scale
    # ------------------------------------------------------------------

    @property
    def scale(self) -> float:
        """Current scale multiplier (1.0 = 128 px base size)."""
        return self._size / self.BASE_SIZE

    def set_scale(self, scale: float) -> None:
        """Set the pet size from a scale multiplier, clamped to [32, 512]."""
        new_size = int(self.BASE_SIZE * scale)
        new_size = max(self.MIN_SIZE, min(self.MAX_SIZE, new_size))
        self._apply_resize(new_size)

    def _apply_resize(self, new_size: int) -> None:
        """Internal: resize window + renderer + mask to a new square size."""
        if new_size == self._size:
            return
        self._size = new_size
        self.setFixedSize(new_size, new_size)
        self._renderer.set_size(new_size, new_size)
        self._set_alpha_mask()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Resize the pet on mouse scroll (±10% per step)."""
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
        """Accept the drag if it contains a local image file URL."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path_lower = url.toLocalFile().lower()
                    if path_lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                        event.acceptProposedAction()
                        return
        event.ignore()

    def dropEvent(self, event) -> None:
        """Replace the pet image with the dropped file."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                        self.set_image(file_path)
                        self.pet_image_changed.emit(file_path)
                        print(f"[DROP] Pet image changed: {file_path}")
                        return

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

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Feed the pet on double-click (for testing the status engine)."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.feed_requested.emit()
            event.accept()

    def closeEvent(self, event) -> None:
        """Clean up when the window is closed."""
        print("PetWindow closed.")
        event.accept()
