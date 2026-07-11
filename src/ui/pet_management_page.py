"""Pet management page: card grid of all pets with switch / delete actions."""
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QLabel,
    QMenu, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)


def _add_shadow(widget: QWidget) -> None:
    """Apply a subtle drop-shadow to a card."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(16)
    effect.setOffset(0, 3)
    effect.setColor(Qt.GlobalColor.black)
    widget.setGraphicsEffect(effect)


class PetManagementPage(QWidget):
    """Card grid showing all saved pets with switch / delete actions."""

    def __init__(self, pet_service, db_service, parent=None) -> None:
        super().__init__(parent)
        self._pet_svc = pet_service
        self._db = db_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(20)

        # ── Title ──
        title = QLabel("我的桌宠")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("管理您创建的所有桌宠。点击「切换到此」更换桌面显示。")
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
        """Rebuild the pet card grid."""
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        pets = self._pet_svc.get_all_pets()
        if not pets:
            empty = QLabel("暂无桌宠\n\n前往「创建桌宠」创建您的第一只桌宠。")
            empty.setStyleSheet(
                "color: #8b949e; font-size: 14px;"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setMinimumHeight(200)
            self._grid.addWidget(empty, 0, 0)
            return

        cols = max(1, self.width() // 300)
        for i, pet in enumerate(pets):
            card = self._build_pet_card(pet)
            row, col = divmod(i, cols)
            self._grid.addWidget(card, row, col)

    # ------------------------------------------------------------------
    # Card builder
    # ------------------------------------------------------------------

    def _build_pet_card(self, pet: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(280, 260)
        _add_shadow(card)

        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(
            lambda pos, p=pet: self._on_context_menu(pos, p, card)
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

        pix = QPixmap(pet.get("image_path", ""))
        if not pix.isNull():
            thumb.setPixmap(
                pix.scaled(
                    260, 120,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            thumb.setText("🐾")
            thumb.setStyleSheet(
                thumb.styleSheet() + " font-size: 32px;"
            )
        lay.addWidget(thumb)

        # Name row
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name = QLabel(pet.get("name", "未命名"))
        name.setStyleSheet(
            "color: #e6edf3; font-size: 14px; font-weight: 600;"
        )
        name_row.addWidget(name)

        if pet.get("is_active"):
            active = QLabel("● 当前桌宠")
            active.setObjectName("badgeGreen")
            name_row.addWidget(active)
        name_row.addStretch()
        lay.addLayout(name_row)

        # Creation date
        date_lbl = QLabel(f"创建于: {pet.get('created_at', '')}")
        date_lbl.setObjectName("cardSubtitle")
        lay.addWidget(date_lbl)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        if not pet.get("is_active"):
            switch_btn = QPushButton("切换到此")
            switch_btn.setObjectName("smallPrimaryBtn")
            switch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            switch_btn.clicked.connect(
                lambda checked, p=pet: self._switch_to(p)
            )
            btn_row.addWidget(switch_btn)

        del_btn = QPushButton("删除")
        del_btn.setObjectName("smallDangerBtn")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(
            lambda checked, p=pet: self._delete_pet(p)
        )
        btn_row.addWidget(del_btn)

        btn_row.addStretch()
        lay.addLayout(btn_row)

        return card

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _on_context_menu(self, pos, pet: dict, card: QFrame) -> None:
        menu = QMenu(self)

        if not pet.get("is_active"):
            switch_action = menu.addAction("🐾 切换到此桌宠")
            switch_action.triggered.connect(lambda: self._switch_to(pet))

        menu.addSeparator()
        del_action = menu.addAction("🗑 删除")
        del_action.triggered.connect(lambda: self._delete_pet(pet))

        menu.exec(card.mapToGlobal(pos))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _switch_to(self, pet: dict) -> None:
        ok = self._pet_svc.switch_to_pet(pet["id"])
        if ok:
            self.refresh()

    def _delete_pet(self, pet: dict) -> None:
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除桌宠「{pet.get('name', '')}」吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._pet_svc.delete_pet(pet["id"])
            self.refresh()
