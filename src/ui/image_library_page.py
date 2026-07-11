"""Image library page: browse uploaded and processed images with card grid."""
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QLabel,
    QMenu, QScrollArea, QVBoxLayout, QWidget,
)


def _add_shadow(widget: QWidget) -> None:
    """Apply a subtle drop-shadow to a card."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(16)
    effect.setOffset(0, 3)
    effect.setColor(Qt.GlobalColor.black)
    widget.setGraphicsEffect(effect)


class ImageLibraryPage(QWidget):
    """Grid view of all images in the user's library with card layout."""

    def __init__(self, pet_service, image_service, db_service,
                 parent=None) -> None:
        super().__init__(parent)
        self._pet_svc = pet_service
        self._image_svc = image_service
        self._db = db_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(20)

        # ── Title ──
        title = QLabel("我的素材")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("管理您上传和处理的图片素材。右键卡片可快速创建桌宠。")
        subtitle.setObjectName("cardSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # ── Scrollable grid ──
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        self._grid_container = QWidget()
        self._grid = QGridLayout(self._grid_container)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(20)
        scroll.setWidget(self._grid_container)

        layout.addWidget(scroll, 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Rebuild the image card grid."""
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        images = self._pet_svc.get_image_library()
        if not images:
            empty = QLabel("暂无素材\n\n前往「创建桌宠」上传您的第一张图片。")
            empty.setStyleSheet(
                "color: #8b949e; font-size: 14px;"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setMinimumHeight(200)
            self._grid.addWidget(empty, 0, 0)
            return

        cols = max(1, self.width() // 300)
        for i, asset in enumerate(images):
            card = self._build_image_card(asset)
            row, col = divmod(i, cols)
            self._grid.addWidget(card, row, col)

    # ------------------------------------------------------------------
    # Card builder
    # ------------------------------------------------------------------

    def _build_image_card(self, asset: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(280, 230)
        _add_shadow(card)

        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(
            lambda pos, a=asset: self._on_context_menu(pos, a, card)
        )

        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        # Thumbnail
        thumb = QLabel()
        thumb.setFixedHeight(130)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setStyleSheet(
            "background: #0d1117; border-radius: 10px;"
        )

        display_path = asset.get("processed_path") or asset.get(
            "original_path", ""
        )
        pix = QPixmap(display_path)
        if not pix.isNull():
            thumb.setPixmap(
                pix.scaled(
                    260, 120,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            thumb.setText("🖼️")
            thumb.setStyleSheet(
                thumb.styleSheet() + " font-size: 32px;"
            )
        lay.addWidget(thumb)

        # File name
        name = QLabel(asset.get("original_name", "Unknown"))
        name.setStyleSheet(
            "color: #e6edf3; font-size: 14px; font-weight: 600;"
        )
        name.setWordWrap(False)
        name.setToolTip(asset.get("original_name", ""))
        lay.addWidget(name)

        # Meta row (badges)
        meta = QHBoxLayout()
        meta.setSpacing(8)

        fmt = QLabel(asset.get("format", "").upper())
        fmt.setObjectName("badge")
        meta.addWidget(fmt)

        if asset.get("processed_path"):
            status = QLabel("已处理")
            status.setObjectName("badgeGreen")
            meta.addWidget(status)

        if asset.get("is_used"):
            used = QLabel("使用中")
            used.setObjectName("badgeBlue")
            meta.addWidget(used)

        meta.addStretch()

        # Date
        date_lbl = QLabel(asset.get("created_at", ""))
        date_lbl.setObjectName("cardSubtitle")
        meta.addWidget(date_lbl)

        lay.addLayout(meta)

        return card

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _on_context_menu(self, pos, asset: dict, card: QFrame) -> None:
        menu = QMenu(self)

        use_action = menu.addAction("🐾 用作桌宠")
        use_action.triggered.connect(lambda: self._use_as_pet(asset))

        menu.addSeparator()

        del_action = menu.addAction("🗑 删除")
        del_action.triggered.connect(lambda: self._delete_asset(asset))

        menu.exec(card.mapToGlobal(pos))

    def _use_as_pet(self, asset: dict) -> None:
        path = asset.get("processed_path") or asset.get("original_path", "")
        if not path or not Path(path).is_file():
            return
        name = Path(asset.get("original_name", "pet")).stem
        self._pet_svc.create_pet_from_image(
            image_path=path,
            name=name,
            original_image_path=asset.get("original_path", path),
            set_active=True,
        )
        self._pet_svc.update_image_asset(asset["id"], {"is_used": True})
        self.refresh()

    def _delete_asset(self, asset: dict) -> None:
        self._pet_svc.delete_image_asset(asset["id"])
        self.refresh()
