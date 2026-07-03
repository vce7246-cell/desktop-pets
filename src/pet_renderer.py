"""PetRenderer: displays the pet image (static PNG or animated GIF)."""
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel


class PetRenderer:
    """Owns a QLabel that displays the pet image."""

    def __init__(self, parent, image_path: str | None = None) -> None:
        self._label = QLabel(parent)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setScaledContents(True)

        if image_path is None:
            image_path = str(
                Path(__file__).resolve().parent / "assets" / "default_pet.png"
            )

        self._pixmap = QPixmap(image_path)
        self._label.setPixmap(self._pixmap)

    @property
    def label(self) -> QLabel:
        return self._label

    @property
    def pixmap(self) -> QPixmap:
        return self._pixmap
