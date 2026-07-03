"""PetWindow: a transparent, borderless, always-on-top overlay window."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBitmap, QMouseEvent, QPixmap
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from src.pet_renderer import PetRenderer


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
    # Event handlers
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Log clicks that reach the window (should only be on non-transparent pixels)."""
        print(f"Pet clicked! ({event.position().x():.0f}, {event.position().y():.0f})")

    def closeEvent(self, event) -> None:
        """Clean up when the window is closed."""
        print("PetWindow closed.")
        event.accept()
