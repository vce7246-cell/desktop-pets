"""ImageAsset domain model."""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class ImageAsset:
    """Metadata for an image in the user's library.

    Tracks both the original upload and its background-removed variant
    (if one exists).  ``is_used`` is True when this asset is the source
    for the currently active desktop pet.
    """

    original_path: str        # path to the original uploaded image
    original_name: str        # original filename (for display)
    format: str               # file extension without dot, e.g. "png"
    processed_path: str | None = None   # path to background-removed version
    id: str = field(default_factory=lambda: uuid4().hex[:12])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    is_used: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "original_path": self.original_path,
            "original_name": self.original_name,
            "format": self.format,
            "processed_path": self.processed_path,
            "created_at": self.created_at,
            "is_used": self.is_used,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ImageAsset":
        return cls(
            id=d.get("id", uuid4().hex[:12]),
            original_path=d["original_path"],
            original_name=d["original_name"],
            format=d["format"],
            processed_path=d.get("processed_path"),
            created_at=d.get("created_at", ""),
            is_used=d.get("is_used", False),
        )
