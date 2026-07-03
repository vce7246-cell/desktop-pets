# Architecture

> Last updated: 2026-07-03  
> Status: Phase 11 complete — scroll wheel resize operational. All 12 milestones done (Phase 12 = packaging remaining).

## File Purposes

| File | Responsibility |
|---|---|
| `src/main.py` | Entry point: QApplication, QSystemTrayIcon, orchestrates PetWindow + MouseTracker + StateMachine |
| `src/pet_window.py` | PetWindow (QMainWindow): transparent overlay, event handlers, window positioning, scroll-wheel resize |
| `src/state_machine.py` | PetStateMachine: pure logic — reads cursor state → emits state transitions (IDLE/FOLLOW/RUN/EXCITED/DRAGGED) |
| `src/pet_renderer.py` | PetRenderer: QLabel + QPixmap/QMovie for static/GIF display, per-state visual transforms, variable-size rendering |
| `src/mouse_tracker.py` | MouseTracker: QTimer (16ms) polling QCursor.pos(), computes speed, delta, still_duration |
| `src/config.py` | Config: QSettings("DesktopPet", "settings") wrapper — save/load position (pet/x, pet/y), scale (pet/scale), and image path (pet/image_path) |

## Data Flow

```
MouseTracker (cursor pos, speed, still_duration)
       │
       ▼
StateMachine (IDLE / FOLLOW / RUN / EXCITED / DRAGGED)
       │
       ├──► PetWindow.update_position() ──► lerp: pet += (target - pet) * stiffness * dt
       │         │
       │         ▼
       └──► PetRenderer.set_state_visual() ──► QLabel transform / scale / animation
```

## State Machine

See [game-design-document.md](game-design-document.md) §4.3 for the full state diagram and transition rules.

## Config Schema

```
QSettings("DesktopPet", "settings")
  ├── pet/image_path   : str   — path to user's pet image file
  ├── pet/x            : int   — window X position
  ├── pet/y            : int   — window Y position
  └── pet/scale        : float — size multiplier (default 1.0, base=128px)
```

## Size / Scale System

- **Base size:** 128×128 px at scale = 1.0
- **Range:** 32–512 px (scale 0.25× – 4.0×)
- **Control:** mouse scroll wheel (±10% per step)
- **Persistence:** saved as `pet/scale` in QSettings; restored on launch
