# Implementation Plan: Desktop Pet — Base Game

> **Target:** v0.1 → v0.3 (invisible window → alive pet with mouse interaction)  
> **Stack:** Python 3.11+ / PyQt6  
> **Source of truth:** [.game-design-document.md](.game-design-document.md) §4, §7; [.tech-stack.md](.tech-stack.md)

---

## Phase 1: Project Skeleton

### Step 1.1 — Create virtual environment and install dependencies

- [ ] Run `python -m venv venv` from project root.
- [ ] Activate venv (`venv\Scripts\activate` on Windows).
- [ ] Run `pip install PyQt6`.
- [ ] Run `pip freeze > requirements.txt`.

**Test:** `python -c "from PyQt6.QtWidgets import QApplication; print('OK')"` prints `OK` with no errors.

### Step 1.2 — Create directory structure and empty modules

- [ ] Create `src/` directory.
- [ ] Create empty `src/__init__.py`.
- [ ] Create these empty `.py` files under `src/`: `main.py`, `pet_window.py`, `state_machine.py`, `pet_renderer.py`, `mouse_tracker.py`, `config.py`.
- [ ] Create `src/assets/` directory.
- [ ] Add a placeholder `src/assets/default_pet.png` (any 128×128 PNG with transparency; a simple colored circle is fine).

**Test:** `python -c "import src.main; import src.pet_window; import src.state_machine; import src.pet_renderer; import src.mouse_tracker; import src.config; print('All modules importable')"` succeeds.

### Step 1.3 — Skeleton main.py: QApplication starts and exits cleanly

- [ ] In `main.py`, create a minimal `QApplication` instance.
- [ ] Call `app.exec()`.
- [ ] Ensure the process exits when the user presses Ctrl+C in the terminal (handle `KeyboardInterrupt`).

**Test:** Run `python src/main.py`. A Python process starts and sits idle (no window visible). Ctrl+C terminates it cleanly with no traceback.

---

## Phase 2: Invisible Pet Window

### Step 2.1 — PetWindow: transparent, borderless, always-on-top window

- [ ] In `pet_window.py`, subclass `QMainWindow`.
- [ ] Set window flags: `FramelessWindowHint | WindowStaysOnTopHint | Tool`.
- [ ] Set attribute `WA_TranslucentBackground` to `True`.
- [ ] Set the window to a fixed size of 128×128 pixels.
- [ ] Position the window at screen center on startup.
- [ ] In `main.py`, instantiate `PetWindow` and call `.show()` before `app.exec()`.

**Test:** Run `python src/main.py`. An invisible 128×128 window exists (hover over it — cursor should change when over the invisible frame). The window is not in the taskbar. Ctrl+C exits.

### Step 2.2 — Click-through on transparent areas

- [ ] In `PetWindow.__init__`, create a `QBitmap` mask where all pixels are transparent (fully black mask).
- [ ] Call `self.setMask(mask)` so the entire window passes clicks through.
- [ ] Verify that `mousePressEvent` is NOT fired when clicking anywhere on the pet area (because mask blocks all input for now).

**Test:** Run the app. Click where the pet window is — the click should reach whatever window is underneath (e.g., click a desktop icon through the pet). The pet window does not steal focus.

### Step 2.3 — Window closes cleanly via Ctrl+C

- [ ] Ensure `KeyboardInterrupt` in `main.py` calls `app.quit()`.
- [ ] Ensure the `PetWindow` destructor or `closeEvent` runs without errors.

**Test:** Run → Ctrl+C. Process exits immediately with exit code 0. No "QThread" or "event loop" warnings.

---

## Phase 3: Render the Pet Image

### Step 3.1 — PetRenderer: display a static PNG on the transparent window

- [ ] In `pet_renderer.py`, create a class `PetRenderer` that owns a `QLabel`.
- [ ] The `QLabel` loads `src/assets/default_pet.png` via `QPixmap`.
- [ ] `QLabel` is set as the central widget of `PetWindow` (or added via a layout).
- [ ] The label fills the 128×128 window exactly.
- [ ] `PetWindow` now creates a `PetRenderer` in `__init__`.

**Test:** Run the app. A 128×128 image floats on the desktop — no borders, no background. The image has proper alpha (transparent areas of the PNG show the desktop behind it).

### Step 3.2 — Click-through: only transparent pixels pass clicks

- [ ] In `PetWindow`, after the renderer loads the image, extract the pixmap's alpha channel.
- [ ] Convert the alpha channel to a `QBitmap` mask: pixels with alpha > 0 are opaque (block clicks); pixels with alpha = 0 are transparent (pass clicks).
- [ ] Call `self.setMask(alpha_mask)` to apply the per-pixel hit-test.
- [ ] Override `mousePressEvent` in `PetWindow` to print "Pet clicked!" for now.

**Test:** Run the app. Click on the visible pet body → terminal prints "Pet clicked!". Click on transparent areas around the pet → click passes through to the window below. No print.

---

## Phase 4: Mouse Tracking

### Step 4.1 — MouseTracker: poll global cursor position at 60 Hz

- [ ] In `mouse_tracker.py`, create a class `MouseTracker` that wraps a `QTimer` with a 16ms interval.
- [ ] Each tick, call `QCursor.pos()` to get the global cursor position (screen coordinates).
- [ ] Store the current position and the previous-frame position.
- [ ] Expose `current_pos`, `prev_pos`, and `delta` (pixels moved since last tick) as properties.
- [ ] Start the timer when `.start()` is called; stop on `.stop()`.
- [ ] In `main.py`, create a `MouseTracker`, start it, and connect a debug print of `delta` each tick.

**Test:** Run the app. Move the mouse — terminal prints delta values. Stop moving — delta prints 0 or near-zero. The tracker does not miss frames (prints appear at ~60 Hz).

### Step 4.2 — Compute cursor speed (pixels per second)

- [ ] In `MouseTracker`, calculate `speed = delta / 0.016` (pixels per second).
- [ ] Expose `speed` as a property.
- [ ] Keep a rolling average of the last 5 speed samples to smooth jitter. Expose as `smoothed_speed`.

**Test:** Run the app. Move mouse slowly → speed < 300. Flick mouse quickly → speed > 600. Keep mouse still for 2+ seconds → speed = 0. Values are smooth (no wild jumps frame to frame).

---

## Phase 5: State Machine

### Step 5.1 — Define the 4 base states and transitions

- [ ] In `state_machine.py`, create an `Enum` with states: `IDLE`, `FOLLOWING`, `RUNNING`, `EXCITED`.
- [ ] Create a `PetStateMachine` class that holds a `current_state`.
- [ ] Implement the transition function `update(cursor_speed, distance_to_pet, mouse_still_duration)` that returns the new state:
  - `FOLLOWING`: default state when mouse is moving at any speed.
  - `RUNNING`: when `cursor_speed > 600` px/s.
  - `IDLE`: when `mouse_still_duration > 2.0` seconds.
  - `EXCITED`: when `distance_to_pet < 150` pixels AND mouse is moving.
- [ ] State priority (highest wins): EXCITED > RUNNING > IDLE > FOLLOWING.
- [ ] Expose a `state_changed` signal (PyQt signal) that emits `(old_state, new_state)` on transition.
- [ ] **No hysteresis in v1** — direct transitions are OK. Smoothing comes later.

**Test (pure logic, no window needed):** Instantiate `PetStateMachine`. Feed it input tuples and assert outputs:

| Input (speed, distance, still_duration) | Expected State |
|---|---|
| (100, 500, 0.0) | FOLLOWING |
| (800, 500, 0.0) | RUNNING |
| (0, 500, 3.0) | IDLE |
| (200, 80, 0.5) | EXCITED |
| (800, 80, 0.0) | EXCITED (priority over RUNNING) |

### Step 5.2 — Wire MouseTracker into StateMachine

- [ ] In `main.py` (or a new orchestrator), connect `MouseTracker` tick → compute `distance_to_pet` (distance from cursor to pet window center).
- [ ] Feed `(speed, distance, still_duration)` into `StateMachine.update()` each tick.
- [ ] Print state transitions to terminal: `[STATE] IDLE → FOLLOWING`.

**Test:** Run the app. Move mouse → see FOLLOWING. Move fast → RUNNING. Stop for 3s → IDLE. Move near the pet → EXCITED. All transitions print to terminal in real time.

### Step 5.3 — Track mouse-still duration

- [ ] In `MouseTracker`, add a `still_timer` that increments by `dt` each tick when `speed < 5` px/s, and resets to 0 when speed exceeds threshold.
- [ ] Expose `still_duration` as a property.

**Test:** Stop mouse. After 1 second, `still_duration ≈ 1.0`. After 3 seconds, `≈ 3.0`. Move mouse briefly → resets to 0.0 immediately.

---

## Phase 6: Pet Motion (Lerp Following)

### Step 6.1 — Implement lerp-based window movement

- [ ] In `PetWindow`, add an `update_position(cursor_pos, stiffness)` method.
- [ ] Compute: `target = cursor_pos + leash_offset` (leash_offset = (20, 20) pixels below-right of cursor).
- [ ] Compute: `new_pos = current_pos + (target - current_pos) * stiffness * dt` where `dt = 0.016`.
- [ ] Move the window with `self.move(new_pos)`.
- [ ] Map stiffness from state machine: FOLLOWING = 3.0, RUNNING = 1.5, IDLE = 0.0.

**Test:** Run the app. Move mouse slowly → pet window smoothly glides toward cursor, slightly lagging. Stop mouse → pet stays in place (stiffness 0). Move fast → pet trails far behind with visible lag.

### Step 6.2 — Motion feels smooth (no jitter)

- [ ] Verify window movement uses integer pixel positions (avoid sub-pixel artifacts).
- [ ] If window appears to "vibrate" near the cursor when close, add a dead zone: if `distance(target, pet) < 5` pixels, skip the move.
- [ ] Ensure `QTimer` is not stacking up callbacks — if an update takes >16ms, skip frames rather than queuing.

**Test:** Move mouse in a smooth circle. Pet follows in a smooth path — no zigzag, no vibration when stationary near mouse. Frame drops (if any) do not cause the pet to "teleport" to catch up.

### Step 6.3 — Apply per-state visual feedback (basic)

- [ ] In `PetRenderer`, add a method `set_state_visual(state)`.
- [ ] For IDLE: apply a subtle scale oscillation by adjusting the `QLabel` transform (or by toggling between two slightly different pixmaps at 1 Hz).
- [ ] For RUNNING: add a slight rotation (±5°) or horizontal stretch.
- [ ] For EXCITED: scale up by 10% (`QLabel.setFixedSize(140, 140)`).
- [ ] For FOLLOWING: default visual (no transform).
- [ ] `PetWindow.update_position()` calls `renderer.set_state_visual(state)` after state changes.

**Test:** Run the app. Observe each state has a visibly different "feel":
- IDLE: pet gently pulses.
- FOLLOWING: pet glides, no transform.
- RUNNING: pet tilts or stretches in movement direction.
- EXCITED: pet grows larger and bounces.

---

## Phase 7: Basic Interaction

### Step 7.1 — Click-and-drag to reposition pet

- [ ] In `PetWindow.mousePressEvent`, record the click offset (cursor position minus window position).
- [ ] Set state to `DRAGGED` (add to state machine enum).
- [ ] In `mouseMoveEvent`, update window position to `cursor_pos - click_offset`.
- [ ] In `mouseReleaseEvent`, return to the appropriate state based on current mouse conditions.
- [ ] While DRAGGED, skip the lerp-based position update (drag takes priority).

**Test:** Run the app. Click on the pet body → hold and drag → pet follows cursor 1:1. Release → pet snaps into FOLLOWING state based on current mouse behavior.

### Step 7.2 — System tray icon with "Quit"

- [ ] In `main.py`, create a `QSystemTrayIcon` with a small icon (16×16 or 32×32 PNG in assets).
- [ ] Create a `QMenu` with a single action: "Quit".
- [ ] Connect "Quit" to `app.quit()`.
- [ ] Call `tray_icon.show()`.
- [ ] The tray icon is visible on app start and persists until quit.

**Test:** Run the app. A tray icon appears in the system notification area. Right-click it → menu with "Quit" appears. Click "Quit" → app exits cleanly. The tray icon disappears after exit.

### Step 7.3 — Pet window hides on Quit with no ghost process

- [ ] In `main.py`, before `app.quit()`, call `pet_window.close()` and `tray_icon.hide()`.
- [ ] Override `PetWindow.closeEvent` to stop the mouse tracker timer and clean up the renderer.

**Test:** Run → Quit via tray → process exits with code 0. No python.exe zombie process in Task Manager.

---

## Phase 8: Configuration Persistence

### Step 8.1 — Config: save and load pet position on exit/startup

- [ ] In `config.py`, create a `Config` class wrapping `QSettings("DesktopPet", "settings")`.
- [ ] On app startup, read saved `pet_x`, `pet_y` (integers). If not found, default to screen center.
- [ ] Apply position to `PetWindow` before `.show()`.
- [ ] On app exit (in `closeEvent` or a shutdown hook), write current `pet.x()`, `pet.y()` to `QSettings`.

**Test:** Run the app. Drag pet to bottom-right corner. Quit. Run again. Pet appears at bottom-right corner. Delete settings (or run on fresh machine) → pet defaults to screen center.

### Step 8.2 — Config: save and load pet image path

- [ ] `Config` stores `pet_image_path` as a string.
- [ ] On startup, if the path exists and file is readable, load it as the pet image.
- [ ] If path is empty or file missing, fall back to `default_pet.png`.
- [ ] `PetRenderer` accepts an optional path override in `__init__`.

**Test:** Manually set settings to a different PNG path. Run → pet shows that image. Delete the file at that path → run again → pet shows default. No crash, no error dialog.

---

## Summary: Milestone Checklist

| # | Step | Milestone |
|---|---|---|
| 1 | Transparent borderless always-on-top window with click-through | M1 ✓ |
| 2 | Pet image rendered with alpha mask hit-testing | M1 ✓ |
| 3 | Mouse tracker polling at 60 Hz with speed + stillness detection | M1 ✓ |
| 4 | State machine: IDLE / FOLLOW / RUN / EXCITED transitions | M2 ✓ |
| 5 | Lerp-based window movement with per-state stiffness | M2 ✓ |
| 6 | Per-state visual transforms (pulse, tilt, scale) | M3 ✓ |
| 7 | Click-and-drag repositioning | M3 ✓ |
| 8 | System tray icon with Quit | M1 ✓ |
| 9 | Config persistence (position + image path) | M2 ✓ |

After completing all 8 phases, the base game is feature-complete: a pet that floats, follows, reacts, and persists.
