# Architecture

> Last updated: 2026-07-03  
> Status: Phase 5 complete — state machine operational with mouse tracking wired in.

## File Purposes

| File | Responsibility |
|---|---|
| `src/main.py` | Entry point: QApplication, QSystemTrayIcon, orchestrates PetWindow + MouseTracker + StateMachine |
| `src/pet_window.py` | PetWindow (QMainWindow): transparent overlay, event handlers, window positioning |
| `src/state_machine.py` | PetStateMachine: pure logic — reads cursor state → emits state transitions (IDLE/FOLLOW/RUN/EXCITED/DRAGGED) |
| `src/pet_renderer.py` | PetRenderer: QLabel + QPixmap/QMovie for static/GIF display, per-state visual transforms |
| `src/mouse_tracker.py` | MouseTracker: QTimer (16ms) polling QCursor.pos(), computes speed, delta, still_duration |
| `src/config.py` | Config: QSettings wrapper — pet image path, window position, size persistence |

## Data Flow

```
MouseTracker (cursor pos, speed, still_duration)
       │
       ▼
StateMachine (IDLE / FOLLOW / RUN / EXCITED / DRAGGED)
       │
       ▼
PetWindow.update_position() ──► window.move(lerped_pos)
       │
       ▼
PetRenderer.set_state_visual() ──► QLabel transform / scale / animation
```

## State Machine

See [game-design-document.md](game-design-document.md) §4.3 for the full state diagram and transition rules.

## Config Schema

```
QSettings("DesktopPet", "settings")
  ├── pet/image_path   : str   — path to user's pet image file
  ├── pet/x            : int   — window X position
  ├── pet/y            : int   — window Y position
  └── pet/scale        : float — size multiplier (default 1.0)
```
