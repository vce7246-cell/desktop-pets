"""PetRenderer: displays the pet image (static PNG or animated GIF)."""
import math
from pathlib import Path

from PyQt6.QtCore import QObject, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QMovie, QPixmap, QTransform
from PyQt6.QtWidgets import QLabel

from src.state_machine import PetState


class PetRenderer(QObject):
    """Owns a QLabel that displays the pet image with per-state visual transforms.

    Supports both static images (QPixmap) and animated GIFs (QMovie).
    For GIFs, per-frame state transforms are skipped — the GIF's own
    animation serves as the visual.
    """

    DEFAULT_SIZE = 128

    # Emitted when a GIF's first frame is ready (so the mask can be refreshed)
    frame_ready = pyqtSignal()

    def __init__(
        self, parent, image_path: str | None = None, size: int = DEFAULT_SIZE,
    ) -> None:
        super().__init__(parent)

        self._label = QLabel(parent)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Current base render size
        self._base_w = size
        self._base_h = size

        if image_path is None:
            image_path = str(
                Path(__file__).resolve().parent / "assets" / "default_pet.png"
            )

        # ---- Rendering state ----
        self._movie: QMovie | None = None
        self._source: QPixmap | None = None   # only for static images
        self._display: QPixmap | None = None  # only for static images

        # Animation state
        self._anim_time: float = 0.0
        self._current_state: PetState | None = None

        # Load the initial image
        self.set_image(image_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def label(self) -> QLabel:
        return self._label

    @property
    def pixmap(self) -> QPixmap:
        """Current display pixmap (used by PetWindow for the alpha mask).

        For animated GIFs, returns the current frame pixmap.
        """
        if self._movie is not None:
            return self._movie.currentPixmap()
        return self._display if self._display is not None else QPixmap()

    @property
    def is_animated(self) -> bool:
        """True when a GIF movie is currently playing."""
        return self._movie is not None

    def set_image(self, image_path: str) -> None:
        """Replace the pet image with a new file (PNG, JPG, GIF, WebP)."""
        # Stop and clean up any previous movie
        if self._movie is not None:
            self._movie.stop()
            self._movie = None
            self._source = None
            self._display = None

        self._anim_time = 0.0
        path_lower = image_path.lower()

        if path_lower.endswith(".gif"):
            # --- Animated GIF mode ---
            self._source = None
            self._display = None
            self._movie = QMovie(image_path, parent=self)
            self._movie.setScaledSize(QSize(self._base_w, self._base_h))
            self._movie.setCacheMode(QMovie.CacheMode.CacheAll)
            self._label.setMovie(self._movie)
            self._movie.start()

            # Notify when the first frame arrives (needed for mask refresh)
            self._movie.frameChanged.connect(self._on_first_gif_frame)
        else:
            # --- Static image mode ---
            self._movie = None
            self._source = QPixmap(image_path)
            self._display = self._source.scaled(
                self._base_w, self._base_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._label.setPixmap(self._display)
            # Emit immediately for static images so mask refreshes without delay
            self.frame_ready.emit()

    def set_size(self, w: int, h: int) -> None:
        """Change the base render size and re-scale the display."""
        self._base_w = w
        self._base_h = h

        if self._movie is not None:
            self._movie.setScaledSize(QSize(w, h))
        elif self._source is not None:
            self._display = self._source.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._label.setPixmap(self._display)

    def set_state_visual(self, state: PetState, dt: float = 0.016) -> None:
        """Apply per-state visual transform to the pet image.

        Called each tick (~60 Hz) by the game loop.

        For animated GIFs, per-frame transforms are skipped — the GIF's
        own animation is the visual. Only static images get transforms.
        """
        # Reset animation phase on state transition
        if state != self._current_state:
            self._anim_time = 0.0
        self._current_state = state
        self._anim_time += dt

        # GIFs: skip per-frame pixmap manipulation
        if self._movie is not None:
            return

        # Static images: apply state-specific transforms
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

    def _on_first_gif_frame(self, frame_number: int) -> None:
        """Called when the QMovie loads a new frame.

        We emit ``frame_ready`` only on frame 0 so the mask is refreshed
        once the first frame of the GIF is available.
        """
        if frame_number == 0:
            movie = self.sender()
            if movie is not None:
                movie.frameChanged.disconnect(self._on_first_gif_frame)
            self.frame_ready.emit()

    def _update_pixmap(self, scale: float, rotation_deg: float) -> None:
        """Generate a display pixmap from the source with given scale and rotation.

        Only called for static images — GIFs skip this path entirely.
        """
        if self._source is None:
            return

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
