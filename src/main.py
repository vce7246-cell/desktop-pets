"""Desktop Pet — entry point."""
import sys
import signal
from pathlib import Path

# Add project root to sys.path so `src` is importable as a package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from src.pet_window import PetWindow
from src.mouse_tracker import MouseTracker
from src.state_machine import PetStateMachine, PetState


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("DesktopPet")
    app.setQuitOnLastWindowClosed(False)

    pet_window = PetWindow()
    pet_window.show()

    # --- Mouse tracker + State machine (Phase 5) ---
    tracker = MouseTracker()
    state_machine = PetStateMachine()

    _tick_count = {"n": 0}
    _prev_state = state_machine.current_state

    def _on_tick():
        _tick_count["n"] += 1
        nonlocal _prev_state

        # Compute distance from cursor to pet window centre
        pet_center = pet_window.frameGeometry().center()
        cursor_pos = tracker.current_pos
        dx = cursor_pos.x() - pet_center.x()
        dy = cursor_pos.y() - pet_center.y()
        distance_to_pet = (dx ** 2 + dy ** 2) ** 0.5

        # --- Determine state: drag overrides everything ---
        if pet_window.is_dragging:
            new_state = PetState.DRAGGED
        else:
            new_state = state_machine.update(
                cursor_speed=tracker.smoothed_speed,
                distance_to_pet=distance_to_pet,
                mouse_still_duration=tracker.still_duration,
            )

        # Print state transitions
        if new_state != _prev_state:
            print(f"[STATE] {_prev_state.name} → {new_state.name}")
            _prev_state = new_state

        # Visual feedback (pet stays in place — no auto-following)
        pet_window.set_pet_state(new_state)

        # Debug output every 15 ticks (~4×/sec)
        if _tick_count["n"] % 15 == 0:
            print(
                f"[TRACKER] speed={tracker.smoothed_speed:6.0f} px/s  "
                f"dist={distance_to_pet:5.0f} px  "
                f"still={tracker.still_duration:4.1f}s  "
                f"state={new_state.name}"
            )

    tracker.ticked.connect(_on_tick)
    tracker.start()

    # Ensure closeEvent fires when app quits
    app.aboutToQuit.connect(pet_window.close)
    app.aboutToQuit.connect(tracker.stop)

    # --- Ctrl+C handling on Windows ---
    # Qt's event loop blocks Python signal delivery. A periodic QTimer
    # forces Python to process pending signals every 100 ms.
    _shutdown = {"flag": False}

    def _on_interrupt(sig, frame):
        _shutdown["flag"] = True

    signal.signal(signal.SIGINT, _on_interrupt)

    def _check_shutdown():
        # Do a tiny Python operation so signals can be delivered
        if _shutdown["flag"]:
            app.quit()

    timer = QTimer()
    timer.timeout.connect(_check_shutdown)
    timer.start(100)

    print("Desktop Pet started. Press Ctrl+C to exit.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
