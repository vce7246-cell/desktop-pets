"""Pet domain model."""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Pet:
    """A desktop pet configuration tracked by the management center.

    Only one pet is ``is_active`` at a time — that pet is displayed
    on the desktop.  Switching pets updates this flag and the QSettings
    image path in one atomic operation inside PetService.
    """

    name: str
    image_path: str           # path to the image currently shown (processed or original)
    original_image_path: str  # path to the original uploaded file
    id: str = field(default_factory=lambda: uuid4().hex[:12])
    scale: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    is_active: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "image_path": self.image_path,
            "original_image_path": self.original_image_path,
            "scale": self.scale,
            "created_at": self.created_at,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Pet":
        return cls(
            id=d.get("id", uuid4().hex[:12]),
            name=d["name"],
            image_path=d["image_path"],
            original_image_path=d.get("original_image_path", d["image_path"]),
            scale=d.get("scale", 1.0),
            created_at=d.get("created_at", ""),
            is_active=d.get("is_active", False),
        )
