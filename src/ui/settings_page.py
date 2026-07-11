"""Settings page: pet scale, display options, and about info."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QSlider, QVBoxLayout, QWidget,
)


class SettingsPage(QWidget):
    """Application settings — scale slider, info, and about section."""

    def __init__(self, db_service, pet_window=None, parent=None) -> None:
        super().__init__(parent)
        self._db = db_service
        self._pet_window = pet_window

        # ── Scrollable container ──
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(24)

        # ── Page title ──
        title = QLabel("设置")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # ══════════════════════════════════════════════════════════════
        # Section: Display
        # ══════════════════════════════════════════════════════════════

        display_section = QLabel("显示")
        display_section.setObjectName("sectionTitle")
        layout.addWidget(display_section)

        # Pet scale slider card
        scale_card = self._build_card()
        scale_layout = QVBoxLayout(scale_card)
        scale_layout.setContentsMargins(24, 20, 24, 20)
        scale_layout.setSpacing(14)

        scale_header = QHBoxLayout()
        scale_title = QLabel("宠物大小")
        scale_title.setObjectName("cardTitle")
        scale_header.addWidget(scale_title)

        self._scale_value_label = QLabel("1.0×")
        self._scale_value_label.setStyleSheet(
            "color: #4f8cff; font-size: 18px; font-weight: 700;"
        )
        scale_header.addStretch()
        scale_header.addWidget(self._scale_value_label)
        scale_layout.addLayout(scale_header)

        scale_desc = QLabel("调整桌宠在桌面上的显示大小。您也可以使用鼠标滚轮直接在桌宠上调整。")
        scale_desc.setObjectName("cardSubtitle")
        scale_desc.setWordWrap(True)
        scale_layout.addWidget(scale_desc)

        # Slider row
        slider_row = QHBoxLayout()
        slider_row.setSpacing(12)

        min_label = QLabel("0.25×")
        min_label.setStyleSheet("color: #6e7681; font-size: 12px;")
        slider_row.addWidget(min_label)

        self._scale_slider = QSlider(Qt.Orientation.Horizontal)
        self._scale_slider.setRange(25, 400)  # 0.25× → 4.0×  (int steps × 100)
        self._scale_slider.setValue(100)       # default 1.0×
        self._scale_slider.setFixedWidth(320)
        self._scale_slider.valueChanged.connect(self._on_scale_changed)
        slider_row.addWidget(self._scale_slider)

        max_label = QLabel("4.0×")
        max_label.setStyleSheet("color: #6e7681; font-size: 12px;")
        slider_row.addWidget(max_label)

        slider_row.addStretch()
        scale_layout.addLayout(slider_row)

        layout.addWidget(scale_card)

        # ══════════════════════════════════════════════════════════════
        # Section: About
        # ══════════════════════════════════════════════════════════════

        about_section = QLabel("关于")
        about_section.setObjectName("sectionTitle")
        layout.addWidget(about_section)

        about_card = self._build_card()
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(24, 20, 24, 20)
        about_layout.setSpacing(8)

        about_title = QLabel("Desktop Pet")
        about_title.setStyleSheet("color: #e6edf3; font-size: 18px; font-weight: 700;")
        about_layout.addWidget(about_title)

        about_version = QLabel("版本 1.0.0")
        about_version.setObjectName("cardSubtitle")
        about_layout.addWidget(about_version)

        about_desc = QLabel(
            "一款跨平台桌面宠物应用。基于 Python + PyQt6 构建。\n"
            "支持图片/GIF 显示、AI 背景去除、物理跟随等特性。"
        )
        about_desc.setObjectName("cardSubtitle")
        about_desc.setWordWrap(True)
        about_desc.setFixedWidth(480)
        about_layout.addWidget(about_desc)

        layout.addWidget(about_card)

        layout.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_card() -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        return card

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _on_scale_changed(self, value: int) -> None:
        scale = value / 100.0
        self._scale_value_label.setText(f"{scale:.2f}×")
        if self._pet_window is not None:
            self._pet_window.set_scale(scale)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Sync slider with current scale (called when page becomes visible)."""
        if self._pet_window is not None:
            current_scale = self._pet_window.scale
            self._scale_slider.blockSignals(True)
            self._scale_slider.setValue(int(current_scale * 100))
            self._scale_slider.blockSignals(False)
            self._scale_value_label.setText(f"{current_scale:.2f}×")
