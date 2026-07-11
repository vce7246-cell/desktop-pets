"""Upload page: drag-and-drop / file-picker → AI processing → create pet."""
from pathlib import Path

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QProgressBar, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget,
)


def _add_shadow(widget: QWidget, radius: int = 20, offset: tuple = (0, 4)) -> None:
    """Apply a drop-shadow effect."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(radius)
    effect.setOffset(*offset)
    effect.setColor(Qt.GlobalColor.black)
    widget.setGraphicsEffect(effect)


class _DropZone(QLabel):
    """A styled drop-target that accepts image files."""

    def __init__(self, on_file, parent=None) -> None:
        super().__init__(parent)
        self._on_file = on_file
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(220)
        self.setObjectName("dropZone")
        self.setText(
            "📁\n\n拖拽图片到此处\n或点击选择文件\n\n"
            "支持 PNG / JPG / GIF / WebP"
        )
        self.setWordWrap(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".webp")
                ):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if path.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".webp")
                    ):
                        self._on_file(path)
                        return

    def mousePressEvent(self, event) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.gif *.webp);;所有文件 (*.*)",
        )
        if file_path:
            self._on_file(file_path)


class UploadPage(QWidget):
    """Step-by-step pet creation: upload → AI process → name → create."""

    STAGE_SELECT = 0
    STAGE_PREVIEW = 1
    STAGE_PROCESSING = 2
    STAGE_RESULT = 3

    def __init__(self, pet_service, image_service, ai_service, db_service,
                 parent=None) -> None:
        super().__init__(parent)
        self._pet_svc = pet_service
        self._image_svc = image_service
        self._ai_svc = ai_service
        self._db = db_service

        self._stage = self.STAGE_SELECT
        self._original_path: str = ""
        self._imported_path: str = ""
        self._processed_path: str = ""
        self._remover_thread: QThread | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(20)

        # ── Title ──
        title = QLabel("创建桌宠")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "上传一张图片，使用 AI 去除背景，然后创建您的专属桌宠。"
        )
        subtitle.setObjectName("cardSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # ── Drop zone ──
        self._drop_zone = _DropZone(self._on_file_selected)
        self._drop_zone.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self._drop_zone, 1)

        # ── Preview row (hidden initially) ──
        self._preview_container = QWidget()
        self._preview_row = QHBoxLayout(self._preview_container)
        self._preview_row.setContentsMargins(0, 0, 0, 0)
        self._preview_row.setSpacing(24)

        self._original_preview = self._make_preview_box("原始图片")
        self._processed_preview = self._make_preview_box("处理后")
        self._preview_row.addWidget(self._original_preview)
        self._preview_row.addWidget(self._processed_preview)
        self._preview_container.hide()
        layout.addWidget(self._preview_container)

        # ── Progress bar ──
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setFixedHeight(4)
        self._progress.setTextVisible(False)
        self._progress.hide()
        layout.addWidget(self._progress)

        # ── Processing status ──
        self._proc_status = QLabel("")
        self._proc_status.setStyleSheet(
            "color: #4f8cff; font-size: 14px; font-weight: 600;"
        )
        self._proc_status.hide()
        layout.addWidget(self._proc_status)

        # ── Action buttons ──
        self._btn_row = QHBoxLayout()
        self._btn_row.setSpacing(12)

        self._remove_bg_btn = QPushButton("🎨 去除背景")
        self._remove_bg_btn.setObjectName("primaryBtn")
        self._remove_bg_btn.clicked.connect(self._on_remove_background)
        self._remove_bg_btn.hide()
        self._btn_row.addWidget(self._remove_bg_btn)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("给桌宠取个名字…")
        self._name_input.setFixedWidth(240)
        self._name_input.setFixedHeight(38)
        self._name_input.hide()
        self._btn_row.addWidget(self._name_input)

        self._create_btn = QPushButton("✅ 创建桌宠")
        self._create_btn.setObjectName("primaryBtn")
        self._create_btn.clicked.connect(self._on_create_pet)
        self._create_btn.hide()
        self._btn_row.addWidget(self._create_btn)

        self._reset_btn = QPushButton("🔄 重新选择")
        self._reset_btn.setObjectName("secondaryBtn")
        self._reset_btn.clicked.connect(self._on_reset)
        self._reset_btn.hide()
        self._btn_row.addWidget(self._reset_btn)

        self._btn_row.addStretch()
        layout.addLayout(self._btn_row)

        # Status label
        self._status = QLabel("")
        self._status.setObjectName("cardSubtitle")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_preview_box(title_text: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(280, 280)
        _add_shadow(card, radius=16, offset=(0, 3))
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        lbl = QLabel(title_text)
        lbl.setObjectName("cardTitle")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl)

        img = QLabel()
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img.setStyleSheet(
            "background: #0d1117; border-radius: 10px;"
        )
        img.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        lay.addWidget(img, 1)
        return card

    @staticmethod
    def _load_pixmap(path: str, max_w: int, max_h: int) -> QPixmap:
        p = QPixmap(path)
        if p.isNull():
            return p
        return p.scaled(
            max_w, max_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _set_stage(self, stage: int) -> None:
        self._stage = stage

        is_select = stage == self.STAGE_SELECT
        is_preview = stage == self.STAGE_PREVIEW
        is_processing = stage == self.STAGE_PROCESSING
        is_result = stage == self.STAGE_RESULT

        self._drop_zone.setVisible(is_select)
        self._preview_container.setVisible(is_preview or is_result)
        self._remove_bg_btn.setVisible(is_preview)
        self._reset_btn.setVisible(is_preview or is_result)

        if is_processing:
            self._progress.show()
            self._proc_status.show()
        else:
            self._progress.hide()
            self._proc_status.hide()

        self._name_input.setVisible(is_result)
        self._create_btn.setVisible(is_result)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_file_selected(self, file_path: str) -> None:
        if not self._image_svc.validate_format(file_path):
            QMessageBox.warning(
                self, "格式不支持",
                "请选择 PNG、JPG、GIF 或 WebP 格式的图片。"
            )
            return

        self._original_path = file_path

        # Import to managed storage
        self._imported_path = self._image_svc.import_image(
            file_path, self._db.original_images_dir,
        )

        # Show original preview
        pix = self._load_pixmap(self._imported_path, 240, 200)
        img_label = self._original_preview.findChild(QLabel)
        if img_label:
            img_label.setPixmap(pix)

        # Clear processed side
        proc_label = self._processed_preview.findChild(QLabel)
        if proc_label:
            proc_label.clear()
            proc_label.setText("点击「去除背景」")

        self._processed_path = ""
        self._set_stage(self.STAGE_PREVIEW)
        self._status.setText(f"已选择: {Path(file_path).name}")

    def _on_remove_background(self) -> None:
        if not self._imported_path:
            return

        output_path = self._image_svc.make_output_path(self._imported_path)
        self._remover_thread = self._ai_svc.remove_background(
            self._imported_path, output_path, parent=self,
        )
        self._remover_thread.finished.connect(self._on_process_done)
        self._remover_thread.error.connect(self._on_process_error)
        self._remover_thread.start()

        self._set_stage(self.STAGE_PROCESSING)
        self._proc_status.setText("⏳ 正在去除背景，请稍候…")
        self._status.setText("")

    def _on_process_done(self, path: str) -> None:
        self._processed_path = path
        self._set_stage(self.STAGE_RESULT)

        # Show processed preview
        proc_label = self._processed_preview.findChild(QLabel)
        if proc_label:
            pix = self._load_pixmap(path, 240, 200)
            proc_label.setPixmap(pix)

        # Suggest a name
        original_name = Path(self._original_path).stem
        self._name_input.setText(original_name)

        self._status.setText(
            "✨ 背景去除完成！给宠物取个名字，然后点击「创建桌宠」。"
        )

    def _on_process_error(self, msg: str) -> None:
        self._set_stage(self.STAGE_PREVIEW)
        self._status.setText(f"处理失败: {msg}")
        QMessageBox.warning(self, "去除背景失败", msg)

    def _on_create_pet(self) -> None:
        name = self._name_input.text().strip()
        if not name:
            name = Path(self._original_path).stem

        # Use processed image if available, otherwise original
        image_path = self._processed_path or self._imported_path

        pet = self._pet_svc.create_pet_from_image(
            image_path=image_path,
            name=name,
            original_image_path=self._imported_path,
            set_active=True,
        )

        # Add to image library
        self._pet_svc.add_image_to_library({
            "original_path": self._imported_path,
            "original_name": Path(self._original_path).name,
            "format": self._image_svc.get_format(self._original_path),
            "processed_path": self._processed_path or None,
            "is_used": True,
        })

        QMessageBox.information(
            self, "创建成功",
            f"桌宠「{name}」已创建并显示在桌面上！\n请查看桌面。"
        )
        self._on_reset()

    def _on_reset(self) -> None:
        self._original_path = ""
        self._imported_path = ""
        self._processed_path = ""
        self._name_input.clear()
        self._status.clear()

        # Clear previews
        for card in [self._original_preview, self._processed_preview]:
            lbl = card.findChild(QLabel)
            if lbl:
                lbl.clear()

        self._set_stage(self.STAGE_SELECT)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Called when page becomes visible."""
        pass
