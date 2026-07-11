"""Desktop Pet — entry point.

Responsibilities of this file (UI layer only):
- Create QApplication, PetWindow, QSystemTrayIcon
- Wire MouseTracker → game-loop tick
- Build tray menu actions (delegating business logic to services)
- Handle shutdown (save state → stop timers → quit)
- Ctrl+C signal handling

All business logic lives in src/services/:
  - DatabaseService  → persistence (image path, position, scale)
  - ImageService     → format validation, path generation, default-pet check
  - AIService        → background removal (rembg) and future AI features
  - PetService       → pet lifecycle, hunger engine, image-change coordination
"""
import sys
import signal
from pathlib import Path

# Add project root to sys.path so `src` is importable as a package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QMenu, QMessageBox, QSystemTrayIcon,
)

from src.services.database_service import DatabaseService
from src.services.image_service import ImageService
from src.services.ai_service import AIService
from src.services.pet_service import PetService
from src.ui.main_window import MainWindow
from src.pet_window import PetWindow
from src.mouse_tracker import MouseTracker
from src.state_machine import PetState


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("DesktopPet")
    app.setQuitOnLastWindowClosed(False)

    # ==================================================================
    # Service layer — all business logic lives here
    # ==================================================================
    db = DatabaseService()
    image_svc = ImageService()
    ai_svc = AIService()

    # ==================================================================
    # Restore saved configuration
    # ==================================================================
    image_path = db.load_image_path()
    if image_path is not None and not Path(image_path).is_file():
        print(f"[CONFIG] Saved image not found: {image_path} — using default.")
        image_path = None

    saved_scale = db.load_scale()
    initial_size = int(PetWindow.BASE_SIZE * saved_scale)
    print(f"[CONFIG] Scale loaded: {saved_scale:.2f} → {initial_size}×{initial_size} px")

    # ==================================================================
    # Pet window (display layer)
    # ==================================================================
    pet_window = PetWindow(image_path=image_path, initial_size=initial_size)

    saved_x, saved_y = db.load_position()
    if saved_x is not None and saved_y is not None:
        pet_window.set_position(saved_x, saved_y)

    pet_window.show()

    # Pet service coordinates PetWindow ↔ DatabaseService ↔ PetStatusEngine
    pet_svc = PetService(pet_window, db)

    # ==================================================================
    # Management center window (hidden until user opens via tray)
    # ==================================================================
    center_window = MainWindow(pet_svc, image_svc, ai_svc, db, pet_window=pet_window)
    # MainWindow is created once and shown/hidden; never recreated

    # ==================================================================
    # Mouse tracker → game-loop tick
    # ==================================================================
    tracker = MouseTracker()

    def _on_tick():
        """60 Hz game loop: evaluate state and sync hunger to UI."""
        pet_center = pet_window.frameGeometry().center()
        cursor_pos = tracker.current_pos
        dx = cursor_pos.x() - pet_center.x()
        dy = cursor_pos.y() - pet_center.y()

        # Fixed state: pet stays in IDLE (breathing animation), drag overrides
        if pet_window.is_dragging:
            new_state = PetState.DRAGGED
        else:
            new_state = PetState.IDLE

        pet_window.set_pet_state(new_state)
        pet_window.set_hunger(pet_svc.hunger)

    tracker.ticked.connect(_on_tick)
    tracker.start()

    # ==================================================================
    # Shutdown
    # ==================================================================

    def _do_clean_shutdown():
        """Save state → stop tracker → close window → hide tray → quit."""
        px, py = pet_window.get_position()
        db.save_position(px, py)
        print(f"[CONFIG] Position saved: ({px}, {py})")

        db.save_scale(pet_window.scale)
        print(f"[CONFIG] Scale saved: {pet_window.scale:.2f}")

        tracker.stop()
        pet_window.close()
        center_window.close()
        tray_icon.hide()
        app.quit()

    # ==================================================================
    # System tray (UI layer — delegates business logic to services)
    # ==================================================================
    assets_dir = Path(__file__).resolve().parent / "assets"
    tray_icon_path = str(assets_dir / "default_pet.png")
    tray_icon = QSystemTrayIcon(QIcon(tray_icon_path), parent=app)

    tray_menu = QMenu()

    # --- "更换宠物" action ---
    def _change_pet():
        """Open file dialog → delegate to PetService for display + persistence."""
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "选择宠物图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.gif *.webp);;所有文件 (*.*)",
        )
        if file_path:
            pet_svc.change_image(file_path)
            print(f"[CONFIG] Image path saved: {file_path}")

    change_action = QAction("更换宠物 (&C)…", tray_menu)
    change_action.triggered.connect(_change_pet)
    tray_menu.addAction(change_action)

    # --- "去除背景" action ---
    def _remove_background():
        """Validate → delegate AI processing to AIService → update pet via PetService."""
        # Guard: don't process the built-in default pet
        if pet_svc.is_using_default_pet():
            QMessageBox.information(None, "提示", "默认宠物图片无需去除背景。")
            return

        current_path = pet_svc.current_image_path
        if not Path(current_path).is_file():
            QMessageBox.warning(None, "去除背景失败", "当前图片文件不存在，请先更换宠物图片。")
            return

        output_path = image_svc.make_output_path(current_path)
        remover = ai_svc.remove_background(current_path, output_path, parent=app)
        tray_icon.setToolTip("桌面宠物 — 正在去除背景…")

        def _on_finished(path: str):
            pet_svc.change_image(path)
            tray_icon.setToolTip("桌面宠物")
            tray_icon.showMessage(
                "桌面宠物", "背景去除完成！", QSystemTrayIcon.MessageIcon.Information, 3000,
            )
            print(f"[REMOVE_BG] Done → {path}")

        def _on_error(msg: str):
            tray_icon.setToolTip("桌面宠物")
            QMessageBox.warning(None, "去除背景失败", msg)
            print(f"[REMOVE_BG] Error: {msg}")

        remover.finished.connect(_on_finished)
        remover.error.connect(_on_error)
        remover.start()

    remove_bg_action = QAction("去除背景 (&R)…", tray_menu)
    remove_bg_action.triggered.connect(_remove_background)
    tray_menu.addAction(remove_bg_action)

    tray_menu.addSeparator()

    # --- "管理中心" action ---
    def _open_center():
        """Show the Desktop Pet Center management window."""
        center_window.show()
        center_window.raise_()
        center_window.activateWindow()

    center_action = QAction("管理中心 (&M)…", tray_menu)
    center_action.triggered.connect(_open_center)
    tray_menu.addAction(center_action)

    tray_menu.addSeparator()

    # --- "退出" action ---
    quit_action = QAction("退出 (&Q)", tray_menu)
    quit_action.triggered.connect(_do_clean_shutdown)
    tray_menu.addAction(quit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("桌面宠物")
    tray_icon.show()

    # ==================================================================
    # App-level lifecycle hooks
    # ==================================================================
    app.aboutToQuit.connect(pet_window.close)
    app.aboutToQuit.connect(center_window.close)
    app.aboutToQuit.connect(tracker.stop)

    # ==================================================================
    # Ctrl+C handling (Windows)
    # ==================================================================
    _shutdown = {"flag": False}

    def _on_interrupt(sig, frame):
        _shutdown["flag"] = True

    signal.signal(signal.SIGINT, _on_interrupt)

    def _check_shutdown():
        if _shutdown["flag"]:
            _do_clean_shutdown()

    signal_timer = QTimer()
    signal_timer.timeout.connect(_check_shutdown)
    signal_timer.start(100)

    print("桌面宠物已启动。右键托盘图标退出，或按 Ctrl+C。")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
