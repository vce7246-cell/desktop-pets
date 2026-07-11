"""Image service: validation, path generation, import, and default-pet detection."""
import shutil
from pathlib import Path
from uuid import uuid4


class ImageService:
    """Stateless image-file utilities used by the UI and other services."""

    SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @classmethod
    def validate_format(cls, path: str) -> bool:
        """Return True if *path* has a supported image extension."""
        return path.lower().endswith(cls.SUPPORTED_EXTENSIONS)

    @classmethod
    def get_format(cls, path: str) -> str:
        """Return the lowercase file extension without dot, e.g. ``"png"``."""
        return Path(path).suffix.lower().lstrip(".")

    @classmethod
    def get_original_name(cls, path: str) -> str:
        """Return the original filename with extension."""
        return Path(path).name

    # ------------------------------------------------------------------
    # Default-pet detection
    # ------------------------------------------------------------------

    @classmethod
    def is_default_pet(cls, path: str) -> bool:
        """Return True if *path* points to the built-in default pet image."""
        default = str(
            Path(__file__).resolve().parent.parent / "assets" / "default_pet.png"
        )
        return path == default

    # ------------------------------------------------------------------
    # Output-path generation
    # ------------------------------------------------------------------

    @classmethod
    def make_output_path(cls, input_path: str) -> str:
        """Generate a non-colliding output path: ``{stem}_nobg.png``.

        If the file already exists, append ``_2``, ``_3``, etc.
        """
        source = Path(input_path)
        parent = source.parent
        stem = source.stem

        candidate = parent / f"{stem}_nobg.png"
        if not candidate.exists():
            return str(candidate)

        n = 2
        while True:
            candidate = parent / f"{stem}_nobg_{n}.png"
            if not candidate.exists():
                return str(candidate)
            n += 1

    # ------------------------------------------------------------------
    # Image import (copy to managed storage)
    # ------------------------------------------------------------------

    @classmethod
    def import_image(cls, source_path: str, dest_dir: Path) -> str:
        """Copy *source_path* into *dest_dir* with a unique name.

        Returns the absolute path to the copied file.
        """
        ext = Path(source_path).suffix.lower()
        unique_name = f"{uuid4().hex[:12]}{ext}"
        dest = dest_dir / unique_name
        shutil.copy2(source_path, dest)
        return str(dest)
