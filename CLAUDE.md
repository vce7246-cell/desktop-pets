# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Desktop Pet — a cross-platform (Windows/macOS) desktop companion app. A borderless, transparent, always-on-top window displays a user-uploaded image/GIF that follows the mouse cursor with physics-based motion and reacts to cursor speed/proximity via a state machine. Built with Python + PyQt6.

Full design: [.game-design-document.md](.game-design-document.md) — see §4.3 for the state machine, §4.4 for tray menu, §7 for the interaction table.

Tech stack rationale: [.tech-stack.md](.tech-stack.md).

## Commands

```bash
# Setup
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
pip install PyQt6 PyInstaller

# Run
python src/main.py

# Package to single exe
pyinstaller --onefile --windowed --add-data "src/assets:assets" src/main.py
```

No tests, linters, or other tooling configured yet — project is pre-code.

## Architecture

### Layered Design (top to bottom)

```
main.py          — QApplication, QSystemTrayIcon, creates PetWindow
pet_window.py    — QMainWindow subclass: transparent overlay, event handlers
state_machine.py — Pure logic: reads cursor state → emits pet state transitions
pet_renderer.py  — QLabel + QMovie for static/GIF display, CSS-style transform overlays
mouse_tracker.py — QTimer (16ms) polling QCursor.pos(), computes speed/Δdistance
config.py        — QSettings wrapper: image path, size, position persistence
```

### State Machine (the core logic)

5 states: **IDLE** → **FOLLOWING** → **RUNNING** → **EXCITED** → **DRAGGED**

Driven entirely by cursor behavior (see GDD §4.3 for diagram):

| State | Trigger | Stiffness | Visual |
|---|---|---|---|
| IDLE | Mouse stationary >2s | 0 (static) | Scale pulse ±2%, blink |
| FOLLOWING | Mouse <300 px/s | 3.0 | Lerp toward cursor + offset |
| RUNNING | Mouse >600 px/s | 1.5 | Lagged trail with overshoot |
| EXCITED | Cursor within 150px of pet | — | Bounce/scale up 10% |
| DRAGGED | Click on non-transparent pixel | — | Attach to cursor until release |

### Tether Math

```
target = cursor_pos + leash_offset
pet_pos += (target - pet_pos) * stiffness * dt
```

`stiffness` is state-dependent (higher = tighter follow). `leash_offset` defaults to below-right of cursor.

### Window Platform Requirements

| Requirement | PyQt6 Implementation |
|---|---|
| Always-on-top | `Qt.WindowStaysOnTopHint` |
| Borderless | `Qt.FramelessWindowHint` |
| Transparent background | `Qt.WA_TranslucentBackground` |
| Click-through on transparent pixels | `setMask(alpha_bitmap)` — only non-alpha pixels receive mouse events |
| No taskbar entry | `Qt.Tool` flag (hides from taskbar/Alt+Tab) |
| Tray-only presence | `QSystemTrayIcon` with context menu; no persistent main window |

# IMPORTANT:
# Always read memory-bank/@architecture.md before writing any code. Include entire database schema.
# Always read memory-bank/@game-design-document.md before writing any code.
# After adding a major feature or completing a milestone, update memory-bank/@architecture.md.
