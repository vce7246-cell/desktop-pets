"""Desktop Pet — entry point."""
import sys
import signal
from pathlib import Path

# Add project root to sys.path so `src` is importable as a package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QFileDialog, QMenu, QSystemTrayIcon

from src.config import Config
from src.pet_window import PetWindow
from src.mouse_tracker import MouseTracker
from src.state_machine import PetStateMachine, PetState


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("DesktopPet")
    app.setQuitOnLastWindowClosed(False)

    # --- Config persistence ---
    config = Config()

    # Load saved image path; fall back to default if missing or unreadable
    image_path = config.load_image_path()
    if image_path is not None and not Path(image_path).is_file():
        print(f"[CONFIG] Saved image not found: {image_path} — using default.")
        image_path = None

    pet_window = PetWindow(image_path=image_path)

    # Restore saved position (if available)
    saved_x, saved_y = config.load_position()
    if saved_x is not None and saved_y is not None:
        pet_window.set_position(saved_x, saved_y)

    pet_window.show()

    # --- Persist image path when changed via drag & drop ---
    pet_window.pet_image_changed.connect(config.save_image_path)

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

    # --- Clean shutdown function (Step 7.3) ---
    def _do_clean_shutdown():
        """Shut down cleanly: save position → stop tracker → close window → hide tray → quit."""
        # Save current pet position before closing
        px, py = pet_window.get_position()
        config.save_position(px, py)
        print(f"[CONFIG] Position saved: ({px}, {py})")

        tracker.stop()
        pet_window.close()
        tray_icon.hide()
        app.quit()

    # --- System tray icon (Step 7.2) ---
    assets_dir = Path(__file__).resolve().parent / "assets"
    tray_icon_path = str(assets_dir / "default_pet.png")
    tray_icon = QSystemTrayIcon(QIcon(tray_icon_path), parent=app)

    tray_menu = QMenu()

    # Change Pet action
    def _change_pet():
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "选择宠物图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.gif *.webp);;所有文件 (*.*)",
        )
        if file_path:
            pet_window.set_image(file_path)
            config.save_image_path(file_path)
            print(f"[CONFIG] Image path saved: {file_path}")

    change_action = QAction("更换宠物 (&C)…", tray_menu)
    change_action.triggered.connect(_change_pet)
    tray_menu.addAction(change_action)

    tray_menu.addSeparator()

    quit_action = QAction("退出 (&Q)", tray_menu)
    quit_action.triggered.connect(_do_clean_shutdown)
    tray_menu.addAction(quit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("桌面宠物")
    tray_icon.show()

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
            _do_clean_shutdown()

    signal_timer = QTimer()
    signal_timer.timeout.connect(_check_shutdown)
    signal_timer.start(100)

    print("桌面宠物已启动。右键托盘图标退出，或按 Ctrl+C。")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
