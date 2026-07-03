"""Desktop Pet — entry point."""
import sys
import signal

from PyQt6.QtWidgets import QApplication


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("DesktopPet")
    app.setQuitOnLastWindowClosed(False)

    # Allow clean exit via Ctrl+C
    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())

    print("Desktop Pet started. Press Ctrl+C to exit.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
