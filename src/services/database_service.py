"""Database service: persistent storage for pet configuration.

Two backends coexist:
1. QSettings (via Config) — window position, scale, last-used image path.
2. SQLite   (via DatabaseManager) — structured data for pets, images, users.
"""
import os
from pathlib import Path

from src.config import Config
from src.database.db_manager import DatabaseManager


def _get_data_dir() -> Path:
    """Return the platform-appropriate app-data directory."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home() / ".local" / "share"
    data_dir = base / "DesktopPet"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


class DatabaseService:
    """Service-layer persistence.

    QSettings (via Config):
        pet/x, pet/y          — window position
        pet/scale             — size multiplier
        pet/image_path        — quick-access image path

    SQLite (via DatabaseManager):
        images table          — id, original_path, original_name, format,
                                processed_path, create_time, status, is_used
        pets   table          — id, image_id, pet_name, pet_path,
                                original_image_path, scale, create_time, is_active
        users  table          — id, username, created_at (reserved)
    """

    def __init__(self) -> None:
        self._config = Config()
        self._data_dir = _get_data_dir()

        # ---- SQLite backend ----
        db_path = self._data_dir / "desktop_pet.db"
        self._db = DatabaseManager(str(db_path))

        # ---- Image storage directories ----
        self._images_original = self._data_dir / "images" / "original"
        self._images_processed = self._data_dir / "images" / "processed"
        self._images_original.mkdir(parents=True, exist_ok=True)
        self._images_processed.mkdir(parents=True, exist_ok=True)

    # ==================================================================
    # QSettings wrappers (unchanged)
    # ==================================================================

    def save_image_path(self, path: str) -> None:
        self._config.save_image_path(path)

    def load_image_path(self) -> str | None:
        return self._config.load_image_path()

    def save_position(self, x: int, y: int) -> None:
        self._config.save_position(x, y)

    def load_position(self) -> tuple[int | None, int | None]:
        return self._config.load_position()

    def save_scale(self, scale: float) -> None:
        self._config.save_scale(scale)

    def load_scale(self) -> float:
        return self._config.load_scale()

    # ==================================================================
    # Image storage paths
    # ==================================================================

    @property
    def original_images_dir(self) -> Path:
        return self._images_original

    @property
    def processed_images_dir(self) -> Path:
        return self._images_processed

    # ==================================================================
    # Pet library (SQLite → pets table)
    # ==================================================================

    def load_all_pets(self) -> list[dict]:
        return self._db.get_all_pets()

    def add_pet(self, pet: dict) -> None:
        self._db.add_pet(pet)

    def update_pet(self, pet_id: int, updates: dict) -> None:
        self._db.update_pet(pet_id, updates)

    def delete_pet(self, pet_id: int) -> None:
        self._db.delete_pet(pet_id)

    def get_active_pet(self) -> dict | None:
        return self._db.get_active_pet()

    # ==================================================================
    # Image library (SQLite → images table)
    # ==================================================================

    def load_image_library(self) -> list[dict]:
        return self._db.get_all_images()

    def add_image_asset(self, asset: dict) -> None:
        self._db.add_image(asset)

    def update_image_asset(self, asset_id: int, updates: dict) -> None:
        self._db.update_image(asset_id, updates)

    def delete_image_asset(self, asset_id: int) -> None:
        self._db.delete_image(asset_id)
