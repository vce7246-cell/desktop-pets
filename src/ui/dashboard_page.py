"""Dashboard page: overview of current pet, stats, and recent activity."""
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)


def _add_shadow(widget: QWidget, radius: int = 20, offset: tuple = (0, 4),
                color: tuple = (0, 0, 0, 60)) -> None:
    """Apply a drop-shadow effect to *widget*."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(radius)
    effect.setOffset(*offset)
    effect.setColor(Qt.GlobalColor.black)
    widget.setGraphicsEffect(effect)


class DashboardPage(QWidget):
    """Home page showing the currently active pet, stats, and recent activity."""

    def __init__(self, pet_service, db_service, parent=None) -> None:
        super().__init__(parent)
        self._pet_svc = pet_service
        self._db = db_service

        # Outer scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(40, 32, 40, 32)
        self._layout.setSpacing(24)

        # ── Title ──
        title = QLabel("首页")
        title.setObjectName("pageTitle")
        self._layout.addWidget(title)

        # ── Welcome subtitle ──
        self._welcome = QLabel("欢迎回来！这是您的桌面宠物管理中心。")
        self._welcome.setObjectName("cardSubtitle")
        self._layout.addWidget(self._welcome)

        # ── Active pet card ──
        self._active_card = self._build_active_card()
        self._layout.addWidget(self._active_card)

        # ── Stats row ──
        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(16)
        self._layout.addLayout(self._stats_row)

        # ── Recent activity ──
        section = QLabel("最近动态")
        section.setObjectName("sectionTitle")
        self._layout.addWidget(section)

        self._activity_list = QVBoxLayout()
        self._activity_list.setSpacing(8)
        self._layout.addLayout(self._activity_list)

        self._layout.addStretch()

        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def _build_active_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        _add_shadow(card)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(24)

        # Pet thumbnail
        self._active_thumb = QLabel()
        self._active_thumb.setFixedSize(104, 104)
        self._active_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._active_thumb.setStyleSheet(
            "background: #0d1117; border-radius: 14px;"
        )
        card_layout.addWidget(self._active_thumb)

        # Info column
        info = QVBoxLayout()
        info.setSpacing(6)

        self._active_name = QLabel("未创建桌宠")
        self._active_name.setStyleSheet(
            "color: #e6edf3; font-size: 18px; font-weight: 700;"
        )
        info.addWidget(self._active_name)

        self._active_meta = QLabel("使用默认宠物图片")
        self._active_meta.setObjectName("cardSubtitle")
        info.addWidget(self._active_meta)

        self._active_time = QLabel("")
        self._active_time.setObjectName("cardSubtitle")
        info.addWidget(self._active_time)

        # Status badge
        self._active_badge = QLabel("")
        self._active_badge.setMaximumWidth(80)
        info.addWidget(self._active_badge)
        info.addStretch()

        card_layout.addLayout(info)
        card_layout.addStretch()
        return card

    def _build_stat_card(self, icon: str, label: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("statCard")
        card.setFixedHeight(100)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        _add_shadow(card, radius=12, offset=(0, 2))

        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(6)

        header = QHBoxLayout()
        val_label = QLabel(value)
        val_label.setObjectName("statValue")
        header.addWidget(val_label)
        header.addStretch()

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 22px;")
        header.addWidget(icon_lbl)
        lay.addLayout(header)

        desc = QLabel(label)
        desc.setObjectName("statLabel")
        lay.addWidget(desc)
        return card

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Rebuild dynamic content."""
        # Clear stats
        while self._stats_row.count():
            item = self._stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear activity
        while self._activity_list.count():
            item = self._activity_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        pets = self._pet_svc.get_all_pets()
        images = self._pet_svc.get_image_library()
        active = self._pet_svc.get_active_pet_info()

        # ── Active pet ──
        if active:
            self._active_name.setText(active.get("name", "未命名"))
            img_path = active.get("image_path", "")
            self._active_meta.setText(
                f"图片: {Path(img_path).name}" if img_path else ""
            )
            self._active_time.setText(
                f"创建时间: {active.get('created_at', '')}"
            )
            self._active_badge.setText("● 运行中")
            self._active_badge.setObjectName("badgeGreen")

            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                self._active_thumb.setPixmap(
                    pixmap.scaled(
                        96, 96,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        else:
            self._active_name.setText("未创建桌宠")
            self._active_meta.setText(
                "前往「创建桌宠」上传您的第一只宠物图片"
            )
            self._active_time.setText("")
            self._active_badge.setText("")
            self._active_thumb.clear()

        # ── Stats ──
        self._stats_row.addWidget(
            self._build_stat_card("🐾", "桌宠总数", str(len(pets)))
        )
        self._stats_row.addWidget(
            self._build_stat_card("🖼️", "素材图片", str(len(images)))
        )
        processed = sum(1 for a in images if a.get("processed_path"))
        self._stats_row.addWidget(
            self._build_stat_card("✨", "已处理", str(processed))
        )

        # ── Recent activity ──
        all_items: list[tuple[str, str, str]] = []
        for p in pets:
            all_items.append(
                ("🐾", f"创建桌宠「{p.get('name', '')}」", p.get("created_at", ""))
            )
        for a in images:
            all_items.append(
                ("🖼️", f"上传素材「{a.get('original_name', '')}」",
                 a.get("created_at", ""))
            )

        all_items.sort(key=lambda x: x[2], reverse=True)

        if not all_items:
            empty = QLabel("暂无动态。开始创建您的第一只桌宠吧！")
            empty.setObjectName("cardSubtitle")
            empty.setMinimumHeight(60)
            self._activity_list.addWidget(empty)
        else:
            for icon, text, date_str in all_items[:10]:
                row = QHBoxLayout()
                row.setSpacing(10)

                icon_lbl = QLabel(icon)
                icon_lbl.setFixedWidth(28)
                icon_lbl.setStyleSheet("font-size: 16px;")
                row.addWidget(icon_lbl)

                msg = QLabel(text)
                msg.setObjectName("activityText")
                row.addWidget(msg)

                dt = QLabel(date_str)
                dt.setObjectName("activityDate")
                dt.setAlignment(Qt.AlignmentFlag.AlignRight)
                row.addWidget(dt)
                self._activity_list.addLayout(row)
