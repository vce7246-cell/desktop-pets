"""Generate a simple default pet PNG (colored circle with transparency)."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap, QColor, QBrush
from PyQt6.QtWidgets import QApplication
import sys


def main():
    app = QApplication(sys.argv)

    size = 128
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QBrush(QColor("#6C5CE7")))  # purple blob
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(14, 20, 100, 90)  # body
    painter.setBrush(QBrush(QColor("#A29BFE")))  # lighter purple
    painter.drawEllipse(30, 10, 68, 50)   # head
    # eyes
    painter.setBrush(QBrush(QColor("white")))
    painter.drawEllipse(48, 25, 14, 16)
    painter.drawEllipse(68, 25, 14, 16)
    painter.setBrush(QBrush(QColor("#2D3436")))
    painter.drawEllipse(52, 29, 8, 10)
    painter.drawEllipse(72, 29, 8, 10)
    painter.end()

    pixmap.save("src/assets/default_pet.png")
    print("Saved src/assets/default_pet.png")


if __name__ == "__main__":
    main()
