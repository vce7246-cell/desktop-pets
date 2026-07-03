# Progress Tracking

> Last updated: 2026-07-03

## Current Status: Phase 0 — Pre-implementation

No steps completed yet.

---

## Phase 1: Project Skeleton

- [ ] Step 1.1 — Create virtual environment and install dependencies
- [ ] Step 1.2 — Create directory structure and empty modules
- [ ] Step 1.3 — Skeleton main.py: QApplication starts and exits cleanly

## Phase 2: Invisible Pet Window

- [ ] Step 2.1 — Transparent, borderless, always-on-top window
- [ ] Step 2.2 — Click-through on transparent areas
- [ ] Step 2.3 — Window closes cleanly via Ctrl+C

## Phase 3: Render the Pet Image

- [ ] Step 3.1 — Display a static PNG on the transparent window
- [ ] Step 3.2 — Click-through: only transparent pixels pass clicks

## Phase 4: Mouse Tracking

- [ ] Step 4.1 — Poll global cursor position at 60 Hz
- [ ] Step 4.2 — Compute cursor speed (pixels per second)

## Phase 5: State Machine

- [ ] Step 5.1 — Define the 4 base states and transitions
- [ ] Step 5.2 — Wire MouseTracker into StateMachine
- [ ] Step 5.3 — Track mouse-still duration

## Phase 6: Pet Motion

- [ ] Step 6.1 — Implement lerp-based window movement
- [ ] Step 6.2 — Motion feels smooth (no jitter)
- [ ] Step 6.3 — Apply per-state visual feedback

## Phase 7: Basic Interaction

- [ ] Step 7.1 — Click-and-drag to reposition pet
- [ ] Step 7.2 — System tray icon with "Quit"
- [ ] Step 7.3 — Pet window hides on Quit with no ghost process

## Phase 8: Configuration Persistence

- [ ] Step 8.1 — Save and load pet position on exit/startup
- [ ] Step 8.2 — Save and load pet image path
