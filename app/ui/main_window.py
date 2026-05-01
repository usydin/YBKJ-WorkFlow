from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCloseEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_INFO, LOGO_PATH
from app.database import SQLiteDataPool
from app.intake_service import IntakeService
from app.local_config import LocalConfigService
from app.ui.data_entry_page import DataEntryPage
from app.ui.styles import get_stylesheet


NAV_ITEMS = [
    "工作台",
    "数据录入",
    "智能解析",
    "数据池",
    "日报生成",
    "Excel导出",
    "统计分析",
    "模型训练",
    "日志中心",
    "设置",
]

HOME_CARDS = [
    ("今日记录数", "today_record_count"),
    ("火灾报警数量", "0"),
    ("视频监控数量", "0"),
    ("其他装置及设备数量", "0"),
    ("总工时", "0.0"),
    ("待人工确认数量", "pending_confirmation_count"),
]


def load_logo_pixmap(width: int) -> QPixmap | None:
    if not LOGO_PATH.exists():
        return None

    pixmap = QPixmap(str(LOGO_PATH))
    if pixmap.isNull():
        return None

    return pixmap.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)


class DashboardCard(QFrame):
    def __init__(self, title: str, value: str) -> None:
        super().__init__()
        self.setObjectName("DashboardCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")

        self.value_label = QLabel(value)
        self.value_label.setObjectName("CardValue")

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class PlaceholderPage(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("PlaceholderCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("PlaceholderTitle")

        desc_label = QLabel(
            "当前阶段先提供模块骨架与界面占位，后续版本将在此接入实际业务流程、数据处理和导出逻辑。"
        )
        desc_label.setWordWrap(True)
        desc_label.setObjectName("PlaceholderDescription")

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch(1)


class SettingsPage(QFrame):
    def __init__(self, current_theme: str) -> None:
        super().__init__()
        self.setObjectName("PlaceholderCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        title_label = QLabel("设置")
        title_label.setObjectName("PlaceholderTitle")

        desc_label = QLabel("主题设置说明占位页。")
        desc_label.setWordWrap(True)
        desc_label.setObjectName("PlaceholderDescription")

        self.current_theme_label = QLabel()
        self.current_theme_label.setObjectName("MetaText")

        note_label = QLabel("可通过左侧底部按钮切换")
        note_label.setObjectName("MetaText")

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addWidget(self.current_theme_label)
        layout.addWidget(note_label)
        layout.addStretch(1)

        self.set_current_theme(current_theme)

    def set_current_theme(self, theme: str) -> None:
        theme_text = "浅色模式" if theme == "light" else "深色模式"
        self.current_theme_label.setText(f"当前主题：{theme_text}")


class MainWindow(QMainWindow):
    def __init__(
        self,
        data_pool: SQLiteDataPool,
        intake_service: IntakeService,
        local_config_service: LocalConfigService,
        initial_theme: str,
    ) -> None:
        super().__init__()
        self.data_pool = data_pool
        self.intake_service = intake_service
        self.local_config_service = local_config_service
        self.current_theme = initial_theme
        self.logger = logging.getLogger("ybkj_workflow.ui")
        self.dashboard_cards: dict[str, DashboardCard] = {}
        self.setWindowTitle(APP_INFO.project_name_en)
        self.resize(1360, 860)
        self.setMinimumSize(QSize(1180, 760))

        central_widget = QWidget()
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_content_area(), 1)

        self.setCentralWidget(central_widget)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 20, 18, 20)
        layout.setSpacing(16)

        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(12)

        logo_label = self._create_logo_label(44, "YB")
        brand_layout.addWidget(logo_label, 0, Qt.AlignmentFlag.AlignTop)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        brand_title = QLabel(APP_INFO.tool_name)
        brand_title.setObjectName("SidebarTitle")
        brand_subtitle = QLabel(APP_INFO.project_name_en)
        brand_subtitle.setObjectName("SidebarSubtitle")

        title_layout.addWidget(brand_title)
        title_layout.addWidget(brand_subtitle)
        brand_layout.addLayout(title_layout, 1)

        layout.addLayout(brand_layout)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        for index, item in enumerate(NAV_ITEMS):
            button = QPushButton(item)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked, idx=index: self.switch_page(idx))
            self.nav_group.addButton(button, index)
            layout.addWidget(button)
            if index == 0:
                button.setChecked(True)

        layout.addItem(
            QSpacerItem(
                20,
                20,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
        )

        offline_tip = QLabel("离线模式已启用\n企业微信接口默认关闭")
        offline_tip.setObjectName("SidebarSubtitle")
        offline_tip.setWordWrap(True)
        self.theme_toggle_button = QPushButton()
        self.theme_toggle_button.setObjectName("ThemeToggleButton")
        self.theme_toggle_button.clicked.connect(self.toggle_theme)
        self._update_theme_toggle_button_text()

        layout.addWidget(self.theme_toggle_button)
        layout.addWidget(offline_tip)

        return sidebar

    def _build_content_area(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        page_title = QLabel(APP_INFO.project_name_cn)
        page_title.setObjectName("AppTitle")
        page_subtitle = QLabel(APP_INFO.product_line)
        page_subtitle.setObjectName("AppSubtitle")

        layout.addWidget(page_title)
        layout.addWidget(page_subtitle)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_home_page())
        self.data_entry_page = DataEntryPage(self.intake_service)
        self.data_entry_page.submitted.connect(self.handle_data_submitted)
        self.stack.addWidget(self._wrap_page(self.data_entry_page))

        for item in NAV_ITEMS[2:-1]:
            self.stack.addWidget(self._wrap_page(PlaceholderPage(item)))
        self.settings_page = SettingsPage(self.current_theme)
        self.stack.addWidget(self._wrap_page(self.settings_page))

        layout.addWidget(self.stack, 1)
        return container

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        content_layout.addWidget(self._build_about_card())

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        for index, (title, value_key) in enumerate(HOME_CARDS):
            row = index // 3
            column = index % 3
            display_value = "0.0" if title == "总工时" else "0"
            card = DashboardCard(title, display_value)
            if value_key in {"today_record_count", "pending_confirmation_count"}:
                self.dashboard_cards[value_key] = card
            grid.addWidget(card, row, column)

        cards_container = QWidget()
        cards_container.setLayout(grid)
        content_layout.addWidget(cards_container)

        scroll_area.setWidget(scroll_content)
        page_layout.addWidget(scroll_area)
        self.refresh_dashboard()
        return page

    def _build_about_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("HeaderCard")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        layout.addWidget(self._create_logo_label(88, "YB"), 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)

        title_label = QLabel(APP_INFO.project_name_cn)
        title_label.setObjectName("AppTitle")

        product_label = QLabel(APP_INFO.product_line)
        product_label.setObjectName("AppSubtitle")

        version_label = QLabel(f"Version: {APP_INFO.version}")
        version_label.setObjectName("MetaText")
        developer_label = QLabel(f"Developer: {APP_INFO.developer}")
        developer_label.setObjectName("MetaText")
        copyright_label = QLabel(APP_INFO.copyright_text)
        copyright_label.setObjectName("MetaText")

        text_layout.addWidget(title_label)
        text_layout.addWidget(product_label)
        text_layout.addWidget(version_label)
        text_layout.addWidget(developer_label)
        text_layout.addWidget(copyright_label)

        layout.addLayout(text_layout, 1)
        return card

    def _create_logo_label(self, size: int, fallback_text: str) -> QLabel:
        label = QLabel()
        label.setFixedSize(size, size)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            "background-color: #1E293B; border-radius: 12px; color: #BFDBFE; font-weight: 700;"
        )

        pixmap = load_logo_pixmap(size)
        if pixmap is None:
            label.setText(fallback_text)
            self.logger.info("Logo not found, using fallback text.")
        else:
            label.setPixmap(pixmap)
            label.setStyleSheet("background-color: transparent;")

        return label

    def _wrap_page(self, page: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(page)
        return container

    def switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.logger.info("Switched to page: %s", NAV_ITEMS[index])

    def refresh_dashboard(self) -> None:
        counts = self.data_pool.get_dashboard_counts()
        if "today_record_count" in self.dashboard_cards:
            self.dashboard_cards["today_record_count"].set_value(
                str(counts["today_record_count"])
            )
        if "pending_confirmation_count" in self.dashboard_cards:
            self.dashboard_cards["pending_confirmation_count"].set_value(
                str(counts["pending_confirmation_count"])
            )

    def handle_data_submitted(self) -> None:
        self.refresh_dashboard()
        self.statusBar().showMessage("录入内容已提交到待解析队列。", 3000)

    def toggle_theme(self) -> None:
        next_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme(next_theme)
        self.local_config_service.save_theme(next_theme)
        self.statusBar().showMessage(f"主题已切换为：{'浅色模式' if next_theme == 'light' else '深色模式'}", 3000)

    def apply_theme(self, theme: str) -> None:
        self.current_theme = "light" if theme == "light" else "dark"
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(get_stylesheet(self.current_theme))
        self._update_theme_toggle_button_text()
        self.settings_page.set_current_theme(self.current_theme)
        self.logger.info("Theme switched: %s", self.current_theme)

    def _update_theme_toggle_button_text(self) -> None:
        if self.current_theme == "light":
            self.theme_toggle_button.setText("🌙 深色模式")
        else:
            self.theme_toggle_button.setText("☀ 浅色模式")

    def closeEvent(self, event: QCloseEvent) -> None:
        self.logger.info("Main window close requested")
        super().closeEvent(event)
