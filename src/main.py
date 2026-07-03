"""Desktop Pet — entry point."""
import sys
import signal
from pathlib import Path

# Add project root to sys.path so `src` is importable as a package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from src.pet_window import PetWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("DesktopPet")
    app.setQuitOnLastWindowClosed(False)

    pet_window = PetWindow()
    pet_window.show()

    # Ensure closeEvent fires when app quits
    app.aboutToQuit.connect(pet_window.close)

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
