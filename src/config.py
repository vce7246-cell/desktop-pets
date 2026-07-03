"""Config: QSettings wrapper for pet position, image path, and scale."""
from PyQt6.QtCore import QSettings


class Config:
    """Wraps QSettings("DesktopPet", "settings") for pet config persistence."""

    def __init__(self) -> None:
        self._settings = QSettings("DesktopPet", "settings")

    # ------------------------------------------------------------------
    # Position
    # ------------------------------------------------------------------

    def save_position(self, x: int, y: int) -> None:
        """Persist the pet window's current screen position."""
        self._settings.setValue("pet/x", x)
        self._settings.setValue("pet/y", y)

    def load_position(self) -> tuple[int | None, int | None]:
        """Return saved (x, y) position, or (None, None) if never saved.

        Values are rounded to int because QPoint expects integers.
        """
        x = self._settings.value("pet/x")
        y = self._settings.value("pet/y")
        if x is not None and y is not None:
            return int(x), int(y)
        return None, None

    # ------------------------------------------------------------------
    # Image path
    # ------------------------------------------------------------------

    def save_image_path(self, path: str) -> None:
        """Persist the path to the user's chosen pet image."""
        self._settings.setValue("pet/image_path", path)

    def load_image_path(self) -> str | None:
        """Return the saved image path, or None if never set."""
        path = self._settings.value("pet/image_path")
        return str(path) if path else None
