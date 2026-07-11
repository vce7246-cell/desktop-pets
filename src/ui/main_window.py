"""MainWindow: Desktop Pet Center with sidebar navigation + stacked pages.

Design: Dark Modern Pro — inspired by Wallpaper Engine / Steam client.
"""
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QStackedWidget, QVBoxLayout, QWidget,
)

from src.ui.dashboard_page import DashboardPage
from src.ui.upload_page import UploadPage
from src.ui.image_library_page import ImageLibraryPage
from src.ui.pet_management_page import PetManagementPage
from src.ui.settings_page import SettingsPage


# ======================================================================
# Global Stylesheet — Dark Modern Pro
# ======================================================================

STYLESHEET = """
/* ================================================================
   Desktop Pet Center — Dark Modern Pro Theme
   ================================================================ */

/* ---- Base ---- */
QMainWindow {
    background: #0d1117;
}

/* ---- Sidebar ---- */
#sidebar {
    background: #0a0e13;
    border: none;
    border-right: 1px solid #21262d;
    padding: 8px 0px;
    font-size: 14px;
    color: #8b949e;
    outline: none;
}
#sidebar::item {
    padding: 10px 16px;
    margin: 1px 8px;
    border-radius: 8px;
    color: #8b949e;
}
#sidebar::item:selected {
    background: rgba(79, 140, 255, 0.15);
    color: #e6edf3;
}
#sidebar::item:hover:!selected {
    background: rgba(255, 255, 255, 0.04);
    color: #c9d1d9;
}

/* ---- Page titles ---- */
#pageTitle {
    font-size: 24px;
    font-weight: 700;
    color: #e6edf3;
    padding: 0px;
}
#sectionTitle {
    font-size: 16px;
    font-weight: 600;
    color: #c9d1d9;
    margin-top: 4px;
}

/* ---- Cards ---- */
#card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
}
#card:hover {
    border: 1px solid #4f8cff;
}
#cardTitle {
    font-size: 15px;
    font-weight: 600;
    color: #e6edf3;
}
#cardSubtitle {
    font-size: 13px;
    color: #8b949e;
}

/* ---- Stat cards ---- */
#statCard {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
}
#statValue {
    font-size: 28px;
    font-weight: 700;
    color: #4f8cff;
}
#statLabel {
    font-size: 13px;
    color: #8b949e;
}

/* ---- Activity feed ---- */
#activityText {
    font-size: 13px;
    color: #c9d1d9;
}
#activityDate {
    font-size: 12px;
    color: #6e7681;
}

/* ---- Drop zone ---- */
#dropZone {
    background: #161b22;
    border: 2px dashed #30363d;
    border-radius: 16px;
    font-size: 15px;
    color: #8b949e;
    padding: 32px;
}
#dropZone:hover {
    border-color: #4f8cff;
    background: #1a1f2b;
}

/* ---- Buttons ---- */
#primaryBtn {
    background: #4f8cff;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 600;
}
#primaryBtn:hover {
    background: #3b6fd4;
}
#primaryBtn:pressed {
    background: #2c5bb5;
}
#primaryBtn:disabled {
    background: #21262d;
    color: #484f58;
}

#secondaryBtn {
    background: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
}
#secondaryBtn:hover {
    background: #30363d;
    border-color: #4f8cff;
}

#smallPrimaryBtn {
    background: #4f8cff;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}
#smallPrimaryBtn:hover {
    background: #3b6fd4;
}

#smallDangerBtn {
    background: transparent;
    color: #f85149;
    border: 1px solid #3d1f1f;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
}
#smallDangerBtn:hover {
    background: rgba(248, 81, 73, 0.1);
    border-color: #f85149;
}

/* ---- Badges ---- */
#badge {
    background: #21262d;
    color: #8b949e;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}
#badgeGreen {
    background: rgba(63, 185, 80, 0.15);
    color: #3fb950;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}
#badgeBlue {
    background: rgba(79, 140, 255, 0.15);
    color: #4f8cff;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

/* ---- Inputs ---- */
QLineEdit {
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 14px;
    color: #e6edf3;
    background: #0d1117;
}
QLineEdit:focus {
    border-color: #4f8cff;
}
QLineEdit::placeholder {
    color: #484f58;
}

/* ---- Progress bar ---- */
QProgressBar {
    background: #21262d;
    border: none;
    border-radius: 3px;
}
QProgressBar::chunk {
    background: #4f8cff;
    border-radius: 3px;
}

/* ---- Sliders ---- */
QSlider::groove:horizontal {
    background: #21262d;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #4f8cff;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}
QSlider::handle:horizontal:hover {
    background: #3b6fd4;
}
QSlider::sub-page:horizontal {
    background: #4f8cff;
    border-radius: 3px;
}

/* ---- Checkboxes ---- */
QCheckBox {
    color: #c9d1d9;
    font-size: 14px;
    spacing: 10px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #30363d;
    border-radius: 4px;
    background: #0d1117;
}
QCheckBox::indicator:checked {
    background: #4f8cff;
    border-color: #4f8cff;
}

/* ---- Scrollbars ---- */
QScrollArea {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #484f58;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
}
QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #484f58;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ---- Menu (context menus) ---- */
QMenu {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 4px;
    color: #c9d1d9;
}
QMenu::item {
    padding: 8px 32px 8px 16px;
    border-radius: 4px;
}
QMenu::item:selected {
    background: #1f6feb;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background: #30363d;
    margin: 4px 8px;
}

/* ---- Message box (approximate via dialog styling) ---- */
QMessageBox {
    background: #161b22;
    color: #c9d1d9;
}
QLabel {
    color: #c9d1d9;
}
"""

# ======================================================================
# Sidebar items
# ======================================================================

SIDEBAR_ITEMS = [
    ("🏠  首页", 0),
    ("✨  创建桌宠", 1),
    ("🖼️  我的素材", 2),
    ("🐾  我的桌宠", 3),
    ("⚙️  设置", 4),
]


class MainWindow(QMainWindow):
    """Desktop Pet Center — the main management window.

    Layout::

        ┌────────────┬──────────────────────────┐
        │  Sidebar   │  QStackedWidget            │
        │  (240px)   │                            │
        │            │  Page 0: Dashboard          │
        │  首页       │  Page 1: Upload             │
        │  创建桌宠   │  Page 2: Image Library      │
        │  我的素材   │  Page 3: Pet Management     │
        │  我的桌宠   │  Page 4: Settings            │
        │  设置       │                            │
        └────────────┴──────────────────────────┘
    """

    WINDOW_TITLE = "Desktop Pet Center"
    MIN_WIDTH = 900
    MIN_HEIGHT = 640
    SIDEBAR_WIDTH = 240

    def __init__(
        self, pet_service, image_service, ai_service, db_service,
        pet_window=None, parent=None,
    ) -> None:
        super().__init__(parent)
        self._pet_svc = pet_service
        self._image_svc = image_service
        self._ai_svc = ai_service
        self._db = db_service
        self._pet_window = pet_window

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.resize(1000, 700)

        # Apply global stylesheet
        self.setStyleSheet(STYLESHEET)

        # ── Central widget ──
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──
        sidebar = QWidget()
        sidebar.setFixedWidth(self.SIDEBAR_WIDTH)
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 16, 0, 16)
        sidebar_layout.setSpacing(0)

        # Logo / brand
        logo = QLabel("🐾  Desktop Pet")
        logo.setStyleSheet(
            "color: #e6edf3; font-size: 17px; font-weight: 700; "
            "padding: 12px 20px 24px 20px;"
        )
        sidebar_layout.addWidget(logo)

        # Navigation list
        self._sidebar = QListWidget()
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setIconSize(QSize(20, 20))
        self._sidebar.setSpacing(1)

        for text, _ in SIDEBAR_ITEMS:
            item = QListWidgetItem(text)
            item.setSizeHint(QSize(0, 44))
            self._sidebar.addItem(item)

        self._sidebar.currentRowChanged.connect(self._on_nav_changed)
        sidebar_layout.addWidget(self._sidebar, 1)

        # Bottom hint
        version_hint = QLabel("v1.0.0")
        version_hint.setStyleSheet(
            "color: #484f58; font-size: 11px; padding: 12px 20px 4px 20px;"
        )
        sidebar_layout.addWidget(version_hint)

        root.addWidget(sidebar)

        # ── Stacked pages ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: #0d1117;")

        self._pages = [
            DashboardPage(self._pet_svc, self._db),
            UploadPage(self._pet_svc, self._image_svc, self._ai_svc, self._db),
            ImageLibraryPage(self._pet_svc, self._image_svc, self._db),
            PetManagementPage(self._pet_svc, self._db),
            SettingsPage(self._db, pet_window=self._pet_window),
        ]
        for page in self._pages:
            self._stack.addWidget(page)

        root.addWidget(self._stack, 1)

        # Select first item by default
        self._sidebar.setCurrentRow(0)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _on_nav_changed(self, index: int) -> None:
        """Switch the stacked widget and refresh the target page."""
        if 0 <= index < len(self._pages):
            self._stack.setCurrentIndex(index)
            page = self._pages[index]
            if hasattr(page, "refresh"):
                page.refresh()

    def showEvent(self, event) -> None:
        """Refresh the current page each time the window is shown."""
        super().showEvent(event)
        current = self._stack.currentWidget()
        if current is not None and hasattr(current, "refresh"):
            current.refresh()
