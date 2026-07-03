"""PetRenderer: displays the pet image (static PNG or animated GIF)."""
import math
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QTransform
from PyQt6.QtWidgets import QLabel

from src.state_machine import PetState


class PetRenderer:
    """Owns a QLabel that displays the pet image with per-state visual transforms."""

    def __init__(self, parent, image_path: str | None = None) -> None:
        self._label = QLabel(parent)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if image_path is None:
            image_path = str(
                Path(__file__).resolve().parent / "assets" / "default_pet.png"
            )

        # Keep the original pixmap untouched — all transforms derive from this.
        self._source = QPixmap(image_path)

        # Display pixmap (initially scale source to fill the 128×128 window).
        self._display = self._source.scaled(
            128, 128,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(self._display)

        # Animation state
        self._anim_time: float = 0.0
        self._current_state: PetState | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def label(self) -> QLabel:
        return self._label

    @property
    def pixmap(self) -> QPixmap:
        """Current display pixmap (used by PetWindow for the alpha mask)."""
        return self._display

    def set_image(self, image_path: str) -> None:
        """Replace the pet image with a new file (PNG, JPG, GIF, WebP)."""
        self._source = QPixmap(image_path)
        self._display = self._source.scaled(
            128, 128,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(self._display)
        self._anim_time = 0.0

    def set_state_visual(self, state: PetState, dt: float = 0.016) -> None:
        """Apply per-state visual transform to the pet image.

        Called each tick (~60 Hz) by the game loop.
        """
        # Reset animation phase on state transition
        if state != self._current_state:
            self._anim_time = 0.0
        self._current_state = state
        self._anim_time += dt

        if state == PetState.IDLE:
            # Subtle breathing: scale oscillation ±2% at ~0.5 Hz
            scale = 1.0 + 0.02 * math.sin(self._anim_time * math.pi)
            self._update_pixmap(scale, 0.0)

        elif state == PetState.RUNNING:
            # Slight tilt in movement direction (alternating ±5°)
            tilt = 5.0 if int(self._anim_time * 2) % 2 == 0 else -5.0
            self._update_pixmap(1.0, tilt)

        elif state == PetState.EXCITED:
            # Scale up 10% + subtle bounce
            bounce = 1.10 + 0.02 * math.sin(self._anim_time * 3 * math.pi)
            self._update_pixmap(bounce, 0.0)

        elif state == PetState.DRAGGED:
            # Slight squash/stretch while being held
            squeeze = 1.0 + 0.03 * math.sin(self._anim_time * 4 * math.pi)
            self._update_pixmap(squeeze, 0.0)

        else:  # FOLLOWING — default, no transform
            self._update_pixmap(1.0, 0.0)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _update_pixmap(self, scale: float, rotation_deg: float) -> None:
        """Generate a display pixmap from the source with given scale and rotation."""
        label_size = self._label.size()
        if label_size.width() == 0 or label_size.height() == 0:
            return  # label not yet laid out

        w = int(label_size.width() * scale)
        h = int(label_size.height() * scale)

        scaled = self._source.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        if rotation_deg != 0.0:
            t = QTransform().rotate(rotation_deg)
            scaled = scaled.transformed(t, Qt.TransformationMode.SmoothTransformation)

        self._display = scaled
        self._label.setPixmap(scaled)
