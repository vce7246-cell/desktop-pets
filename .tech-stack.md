# Tech Stack: Desktop Pet App

> **Decision Date:** 2026-07-03  
> **Status:** Confirmed

---

## Chosen Stack: Python + PyQt6

| Layer | Technology | Version |
|---|---|---|
| **Language** | Python | 3.11+ |
| **GUI Framework** | PyQt6 | 6.x |
| **Packaging** | PyInstaller | 6.x |
| **Package Manager** | pip / venv | built-in |

---

## Why Python + PyQt6

| Concern | PyQt6 Solution |
|---|---|
| **Always-on-top window** | `Qt.WindowStaysOnTopHint` |
| **Borderless + transparent** | `Qt.FramelessWindowHint` + `setAttribute(Qt.WA_TranslucentBackground)` |
| **Click-through on transparent pixels** | `setMask()` with alpha-channel bitmap |
| **Global mouse tracking** | `QCursor.pos()` polled via `QTimer` at 60 Hz (16ms interval) |
| **GIF playback** | `QMovie` on a `QLabel` |
| **Tray icon** | `QSystemTrayIcon` |
| **Drag & drop** | `setAcceptDrops(True)` + `dragEnterEvent` / `dropEvent` |
| **Config persistence** | `json` / `QSettings` |

## Why NOT the alternatives

| Alternative | Rejection Reason |
|---|---|
| **Tauri** | Requires Rust + Node + VS Build Tools (~3 GB toolchain). Overhead not justified for prototype phase. |
| **Electron** | ~150 MB RAM, 200+ MB disk for a single-sprite window. Too heavy. |
| **tkinter** | No reliable transparency or always-on-top on all platforms. |
| **Pygame** | Designed for full-window games, not desktop overlay windows. |

---

## Environment Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate (Windows)
venv\Scripts\activate

# 3. Install dependencies
pip install PyQt6 PyInstaller
```

**No other dependencies needed for v1.** PyQt6 bundles everything: window management, image/GIF rendering, tray icon, drag-drop, and global cursor polling.

---

## Project Structure (Planned)

```
desktop-pets/
├── venv/                    # Python virtual environment
├── src/
│   ├── main.py              # Entry point: QApplication, tray icon setup
│   ├── pet_window.py        # PetWindow: transparent overlay, mouse follow
│   ├── state_machine.py     # Pet state transitions (IDLE/FOLLOW/RUN/EXCITED)
│   ├── pet_renderer.py      # Image/GIF display via QLabel + QMovie
│   ├── mouse_tracker.py     # Global cursor polling via QTimer
│   ├── config.py            # Settings load/save (pet image path, size, position)
│   └── assets/
│       └── default_pet.png  # Built-in default pet
├── .game-design-document.md
├── .tech-stack.md
├── requirements.txt
└── README.md
```

---

## Key PyQt6 APIs Reference

| Feature | API |
|---|---|
| Transparent frameless window | `setWindowFlags(Qt.FramelessWindowHint \| Qt.WindowStaysOnTopHint \| Qt.Tool)` + `setAttribute(Qt.WA_TranslucentBackground)` |
| Click-through mask | `setMask(bitmap)` where non-transparent pixels = opaque |
| GIF animation | `QMovie("pet.gif")` → `QLabel.setMovie(movie)` → `movie.start()` |
| Global cursor position | `QCursor.pos()` |
| 60 Hz update loop | `QTimer` with 16ms interval → `timeout.connect(update)`
| Tray icon | `QSystemTrayIcon.setIcon()` + `setContextMenu()` |
| Drag-drop image | Override `dragEnterEvent`, `dropEvent`; read file path from `QMimeData` |
| Config storage | `QSettings("DesktopPet", "settings")` |

---

## Performance Budget (Targets)

| Metric | Target |
|---|---|
| CPU (idle) | < 3% |
| CPU (mouse following) | < 8% |
| Memory | < 60 MB |
| Startup time | < 1 second |
| Binary size (PyInstaller) | ~40 MB |
