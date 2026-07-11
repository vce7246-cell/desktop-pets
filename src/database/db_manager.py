"""DatabaseManager: SQLite connection, schema init, and CRUD operations.

Column-name translation:
    The DB uses the user-specified schema columns (pet_name, pet_path,
    create_time, ...).  All public methods accept and return Python dicts
    whose keys match the application's convention (name, image_path,
    created_at, ...).  Translation is handled internally via _*_COL_MAP.
"""
import sqlite3
from pathlib import Path
from typing import Any

# ======================================================================
# Schema
# ======================================================================

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT,
    created_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS images (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path   TEXT    NOT NULL,
    original_name   TEXT    NOT NULL DEFAULT '',
    format          TEXT    NOT NULL DEFAULT '',
    processed_path  TEXT,
    create_time     TEXT    DEFAULT (datetime('now','localtime')),
    status          TEXT    DEFAULT 'active',
    is_used         INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pets (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id             INTEGER,
    pet_name             TEXT    NOT NULL,
    pet_path             TEXT    NOT NULL,
    original_image_path  TEXT    DEFAULT '',
    scale                REAL    DEFAULT 1.0,
    create_time          TEXT    DEFAULT (datetime('now','localtime')),
    is_active            INTEGER DEFAULT 0,
    FOREIGN KEY (image_id) REFERENCES images(id)
);
"""

# ======================================================================
# Column-name maps:  DB column  ↔  application dict key
# ======================================================================

_IMAGE_DB_TO_PY = {
    "id": "id",
    "original_path": "original_path",
    "original_name": "original_name",
    "format": "format",
    "processed_path": "processed_path",
    "create_time": "created_at",
    "status": "status",
    "is_used": "is_used",
}

_PET_DB_TO_PY = {
    "id": "id",
    "image_id": "image_id",
    "pet_name": "name",
    "pet_path": "image_path",
    "original_image_path": "original_image_path",
    "scale": "scale",
    "create_time": "created_at",
    "is_active": "is_active",
}

# Reverse maps:  application key  →  DB column
_IMAGE_PY_TO_DB = {v: k for k, v in _IMAGE_DB_TO_PY.items()}
_PET_PY_TO_DB = {v: k for k, v in _PET_DB_TO_PY.items()}


# ======================================================================
# DatabaseManager
# ======================================================================

class DatabaseManager:
    """SQLite storage for the Desktop Pet application.

    Usage::

        db = DatabaseManager("path/to/desktop_pet.db")

        # Images
        images = db.get_all_images()
        img_id = db.add_image({"original_path": "…", "original_name": "cat.png", …})
        db.update_image(img_id, {"processed_path": "…"})
        db.delete_image(img_id)

        # Pets
        pets = db.get_all_pets()
        pet_id = db.add_pet({"name": "MyCat", "image_path": "…", …})
        db.update_pet(pet_id, {"is_active": True})
        db.delete_pet(pet_id)
        active = db.get_active_pet()
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._init_schema()
        except sqlite3.DatabaseError:
            # Database file is corrupt — rename it and start fresh
            import time
            backup = self._db_path.with_suffix(f".corrupt_{int(time.time())}.bak")
            self._db_path.rename(backup)
            print(f"[DB] Corrupt database backed up to {backup.name}, creating new.")
            self._init_schema()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
        except sqlite3.DatabaseError:
            conn.close()
            raise
        return conn

    def _init_schema(self) -> None:
        conn = self._get_conn()
        try:
            conn.executescript(SCHEMA_SQL)
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Row ↔ dict helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dict(row: sqlite3.Row, col_map: dict) -> dict:
        """Convert an sqlite3.Row to a dict using *col_map* for key names."""
        return {
            py_key: row[db_col]
            for db_col, py_key in col_map.items()
            if db_col in row.keys()
        }

    @staticmethod
    def _dict_to_db_cols(data: dict, py_to_db: dict) -> tuple[list[str], list[str], list[Any]]:
        """Return (db_cols, placeholders, values) for INSERT/UPDATE from a Python dict.

        Only keys present in *py_to_db* are included.
        """
        db_cols: list[str] = []
        placeholders: list[str] = []
        values: list[Any] = []
        for py_key, value in data.items():
            db_col = py_to_db.get(py_key)
            if db_col is not None:
                db_cols.append(db_col)
                placeholders.append("?")
                # Convert bool → int for SQLite
                values.append(int(value) if isinstance(value, bool) else value)
        return db_cols, placeholders, values

    # ==================================================================
    # Images CRUD
    # ==================================================================

    def get_all_images(self) -> list[dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM images WHERE status = 'active' ORDER BY create_time DESC"
            ).fetchall()
            return [self._row_to_dict(r, _IMAGE_DB_TO_PY) for r in rows]
        finally:
            conn.close()

    def add_image(self, data: dict) -> int:
        """Insert an image record. Returns the new row id."""
        db_cols, placeholders, values = self._dict_to_db_cols(data, _IMAGE_PY_TO_DB)
        conn = self._get_conn()
        try:
            sql = f"INSERT INTO images ({', '.join(db_cols)}) VALUES ({', '.join(placeholders)})"
            cur = conn.execute(sql, values)
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def update_image(self, image_id: int, updates: dict) -> None:
        db_cols, _, values = self._dict_to_db_cols(updates, _IMAGE_PY_TO_DB)
        if not db_cols:
            return
        set_clause = ", ".join(f"{c} = ?" for c in db_cols)
        conn = self._get_conn()
        try:
            conn.execute(f"UPDATE images SET {set_clause} WHERE id = ?", values + [image_id])
            conn.commit()
        finally:
            conn.close()

    def delete_image(self, image_id: int) -> None:
        conn = self._get_conn()
        try:
            conn.execute("UPDATE images SET status = 'deleted' WHERE id = ?", (image_id,))
            conn.commit()
        finally:
            conn.close()

    # ==================================================================
    # Pets CRUD
    # ==================================================================

    def get_all_pets(self) -> list[dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM pets ORDER BY create_time DESC"
            ).fetchall()
            return [self._row_to_dict(r, _PET_DB_TO_PY) for r in rows]
        finally:
            conn.close()

    def add_pet(self, data: dict) -> int:
        """Insert a pet record. Auto-deactivates other pets if ``is_active`` is True."""
        db_cols, placeholders, values = self._dict_to_db_cols(data, _PET_PY_TO_DB)
        conn = self._get_conn()
        try:
            # Deactivate all other pets when the new one is active
            if data.get("is_active"):
                conn.execute("UPDATE pets SET is_active = 0")

            sql = f"INSERT INTO pets ({', '.join(db_cols)}) VALUES ({', '.join(placeholders)})"
            cur = conn.execute(sql, values)
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def update_pet(self, pet_id: int, updates: dict) -> None:
        db_cols, _, values = self._dict_to_db_cols(updates, _PET_PY_TO_DB)
        if not db_cols:
            return
        conn = self._get_conn()
        try:
            # Deactivate all other pets when activating this one
            if updates.get("is_active"):
                conn.execute("UPDATE pets SET is_active = 0")

            set_clause = ", ".join(f"{c} = ?" for c in db_cols)
            conn.execute(f"UPDATE pets SET {set_clause} WHERE id = ?", values + [pet_id])
            conn.commit()
        finally:
            conn.close()

    def delete_pet(self, pet_id: int) -> None:
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
            conn.commit()
        finally:
            conn.close()

    def get_active_pet(self) -> dict | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM pets WHERE is_active = 1 LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            return self._row_to_dict(row, _PET_DB_TO_PY)
        finally:
            conn.close()
