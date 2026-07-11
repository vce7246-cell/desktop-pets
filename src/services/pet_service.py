"""Pet service: pet lifecycle management and status-engine coordination.

Orchestrates three concerns:
1. Image changes (tray menu, drag-drop) → display + persist
2. Hunger / foraging state → PetStatusEngine
3. Pet library CRUD → DatabaseService (JSON) + QSettings sync
"""
from pathlib import Path

from src.pet_status import PetStatusEngine
from src.services.image_service import ImageService


class PetService:
    """Manages pet lifecycle across PetWindow, DatabaseService, and PetStatusEngine."""

    def __init__(self, pet_window, database) -> None:
        self._pet_window = pet_window
        self._db = database
        self._status_engine = PetStatusEngine()

        # ── Signal wiring ──────────────────────────────────────────
        pet_window.feed_requested.connect(self._status_engine.feed_pet)
        pet_window.pet_image_changed.connect(self._on_image_changed)

    # ==================================================================
    # Image management (quick actions — tray / drag-drop)
    # ==================================================================

    def change_image(self, image_path: str) -> None:
        """Replace the pet image and persist to QSettings."""
        self._pet_window.set_image(image_path)
        self._db.save_image_path(image_path)

    def _on_image_changed(self, image_path: str) -> None:
        """Drag-drop handler: persist path (display already updated)."""
        self._db.save_image_path(image_path)

    @property
    def current_image_path(self) -> str:
        return self._pet_window.current_image_path

    def is_using_default_pet(self) -> bool:
        return ImageService.is_default_pet(self.current_image_path)

    # ==================================================================
    # Pet library CRUD (management center)
    # ==================================================================

    def create_pet_from_image(
        self, image_path: str, name: str, original_image_path: str = "",
        set_active: bool = True,
    ) -> dict:
        """Create a new pet record, optionally setting it as the active desktop pet.

        Returns the new pet dict.
        """
        pet = {
            "name": name,
            "image_path": image_path,
            "original_image_path": original_image_path or image_path,
            "is_active": set_active,
        }
        self._db.add_pet(pet)

        if set_active:
            # Sync to desktop display + QSettings
            self.change_image(image_path)

        return pet

    def switch_to_pet(self, pet_id: int) -> bool:
        """Activate a pet by ID. Returns False if not found."""
        pets = self._db.load_all_pets()
        target = None
        for p in pets:
            if p["id"] == pet_id:
                target = p
                break

        if target is None:
            return False

        self._db.update_pet(pet_id, {"is_active": True})
        self.change_image(target["image_path"])
        return True

    def delete_pet(self, pet_id: int) -> bool:
        """Delete a pet record. If it was active, deactivate first. Returns False if not found."""
        pets = self._db.load_all_pets()
        target = None
        for p in pets:
            if p["id"] == pet_id:
                target = p
                break

        if target is None:
            return False

        # If deleting the active pet, fall back to default or the first remaining
        was_active = target.get("is_active", False)
        self._db.delete_pet(pet_id)

        if was_active:
            remaining = self._db.load_all_pets()
            if remaining:
                next_pet = remaining[0]
                self.switch_to_pet(next_pet["id"])
            else:
                # No pets left — revert to default
                default_path = str(
                    Path(__file__).resolve().parent.parent / "assets" / "default_pet.png"
                )
                self.change_image(default_path)
        return True

    def get_all_pets(self) -> list[dict]:
        return self._db.load_all_pets()

    def get_active_pet_info(self) -> dict | None:
        return self._db.get_active_pet()

    # ==================================================================
    # Image library helpers
    # ==================================================================

    def get_image_library(self) -> list[dict]:
        return self._db.load_image_library()

    def add_image_to_library(self, asset: dict) -> None:
        self._db.add_image_asset(asset)

    def update_image_asset(self, asset_id: int, updates: dict) -> None:
        self._db.update_image_asset(asset_id, updates)

    def delete_image_asset(self, asset_id: int) -> None:
        self._db.delete_image_asset(asset_id)

    # ==================================================================
    # Hunger / status
    # ==================================================================

    @property
    def hunger(self) -> int:
        return self._status_engine.hunger

    def feed(self) -> None:
        self._status_engine.feed_pet()
