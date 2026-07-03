"""PetWindow: a transparent, borderless, always-on-top overlay window."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBitmap, QMouseEvent
from PyQt6.QtWidgets import QWidget


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

        # --- Click-through mask: all-black = all clicks pass through ---
        self._set_full_transparent_mask()

        # --- Center on screen ---
        self._center_on_screen()

    # ------------------------------------------------------------------
    # Mask / hit-testing
    # ------------------------------------------------------------------

    def _set_full_transparent_mask(self) -> None:
        """Set a mask where all pixels are transparent → all clicks pass through."""
        mask = QBitmap(self.size())
        mask.fill(Qt.GlobalColor.black)
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
        """Log clicks that reach the window (for debugging)."""
        print(f"PetWindow clicked at ({event.position().x():.0f}, {event.position().y():.0f})")

    def closeEvent(self, event) -> None:
        """Clean up when the window is closed."""
        print("PetWindow closed.")
        event.accept()
