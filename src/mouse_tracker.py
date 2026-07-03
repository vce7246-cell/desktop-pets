"""MouseTracker: polls global cursor position at 60 Hz and computes speed."""
from collections import deque

from PyQt6.QtCore import QPoint, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QCursor


class MouseTracker(QObject):
    """Polls QCursor.pos() every 16 ms and exposes position, delta, and speed.

    Emits ``ticked`` on each poll so consumers can react without subclassing.
    """

    # Max samples for the rolling speed average
    _SMOOTH_WINDOW = 5

    ticked = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60 Hz
        self._timer.timeout.connect(self._poll)

        self._current_pos: QPoint = QCursor.pos()
        self._prev_pos: QPoint = self._current_pos

        # Rolling buffer for smoothed speed (pixels/sec)
        self._speed_samples: deque[float] = deque(maxlen=self._SMOOTH_WINDOW)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Begin polling at 60 Hz."""
        self._current_pos = QCursor.pos()
        self._prev_pos = self._current_pos
        self._speed_samples.clear()
        self._timer.start()

    def stop(self) -> None:
        """Stop polling."""
        self._timer.stop()

    @property
    def current_pos(self) -> QPoint:
        """Latest global cursor position (screen coordinates)."""
        return self._current_pos

    @property
    def prev_pos(self) -> QPoint:
        """Cursor position from the previous tick."""
        return self._prev_pos

    @property
    def delta(self) -> float:
        """Euclidean distance the cursor moved since the last tick, in pixels."""
        diff = self._current_pos - self._prev_pos
        return (diff.x() ** 2 + diff.y() ** 2) ** 0.5

    @property
    def speed(self) -> float:
        """Instantaneous cursor speed in pixels per second (this tick only)."""
        return self.delta / 0.016

    @property
    def smoothed_speed(self) -> float:
        """Rolling average of the last 5 speed samples (smoothed jitter)."""
        if not self._speed_samples:
            return 0.0
        return sum(self._speed_samples) / len(self._speed_samples)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _poll(self) -> None:
        """Called every 16 ms by the timer."""
        self._prev_pos = self._current_pos
        self._current_pos = QCursor.pos()
        self._speed_samples.append(self.speed)
        self.ticked.emit()
