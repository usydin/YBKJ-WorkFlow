from pathlib import Path


BASE_STYLESHEET = """
QWidget {
    font-family: "PingFang SC", "Hiragino Sans GB", "Heiti SC";
    font-size: 13px;
}
QLabel {
    background: transparent;
}
QLabel#AppTitle {
    font-size: 22px;
    font-weight: 700;
}
QLabel#AppSubtitle {
    font-size: 13px;
}
QLabel#SidebarTitle {
    font-size: 16px;
    font-weight: 700;
}
QLabel#CardValue {
    font-size: 28px;
    font-weight: 700;
}
QLabel#CardTitle {
    font-size: 13px;
}
QLabel#PlaceholderTitle {
    font-size: 18px;
    font-weight: 700;
}
QLabel#PlaceholderDescription {
    line-height: 1.5;
}
QLabel#FieldLabel {
    font-weight: 600;
}
QPushButton#NavButton,
QPushButton#ThemeToggleButton {
    text-align: left;
    padding: 10px 14px;
    border-radius: 10px;
}
QPushButton#PrimaryButton,
QPushButton#SecondaryButton {
    padding: 10px 16px;
    border-radius: 10px;
    font-weight: 600;
}
QLineEdit#InputBox,
QDoubleSpinBox#InputBox,
QTextEdit#InputArea,
QPlainTextEdit#InputArea {
    border-radius: 12px;
    padding: 8px 12px;
}
QComboBox#InputBox {
    border: 1px solid palette(mid);
    border-radius: 10px;
    padding: 7px 32px 7px 12px;
    min-height: 20px;
}
QDoubleSpinBox#InputBox {
    padding-right: 12px;
    min-height: 20px;
}
QComboBox#InputBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border: none;
    background: transparent;
    margin-right: 4px;
}
QComboBox#InputBox::down-arrow {
    width: 12px;
    height: 12px;
}
QTextEdit#InputArea,
QPlainTextEdit#InputArea {
    padding: 14px;
}
QTextEdit#InputArea,
QPlainTextEdit#InputArea,
QTextEdit#InputArea QWidget,
QPlainTextEdit#InputArea QWidget {
    background-clip: padding;
}
QScrollArea {
    border: none;
}
QTableWidget {
    border-radius: 12px;
    gridline-color: transparent;
}
QSplitter::handle {
    border: none;
    border-radius: 4px;
}
QHeaderView::section {
    padding: 8px 10px;
    border: none;
    font-weight: 600;
}
QTabWidget#ConfirmTabs::pane {
    border: 1px solid palette(mid);
    border-radius: 12px;
    margin-top: 8px;
}
QTabWidget#ConfirmTabs QTabBar::tab {
    padding: 8px 14px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 4px;
    font-weight: 600;
}
"""

DARK_STYLESHEET = """
QWidget {
    background-color: #111827;
    color: #E5E7EB;
}
QLabel {
    background: transparent;
}
QMainWindow {
    background-color: #0B1220;
}
QFrame#Sidebar {
    background-color: #0F172A;
    border-right: 1px solid #1F2937;
}
QFrame#HeaderCard, QFrame#DashboardCard, QFrame#PlaceholderCard {
    background-color: #111827;
    border: 1px solid #1F2937;
    border-radius: 16px;
}
QFrame#DetailPanel {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 14px;
}
QLabel#AppTitle {
    color: #F9FAFB;
}
QLabel#AppSubtitle {
    color: #93C5FD;
}
QLabel#MetaText,
QLabel#SidebarSubtitle,
QLabel#CardTitle,
QLabel#PlaceholderDescription {
    color: #9CA3AF;
}
QLabel#FieldLabel {
    color: #CBD5E1;
}
QLabel#MetaBadge {
    background-color: #1E293B;
    color: #93C5FD;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 6px 10px;
}
QLabel#FeedbackLabel {
    color: #86EFAC;
}
QPushButton#NavButton,
QPushButton#ThemeToggleButton {
    border: none;
    background-color: transparent;
    color: #D1D5DB;
}
QPushButton#NavButton:hover,
QPushButton#ThemeToggleButton:hover {
    background-color: #1E293B;
}
QPushButton#NavButton:checked {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 600;
}
QLabel#CardValue {
    color: #F9FAFB;
}
QComboBox#InputBox,
QLineEdit#InputBox,
QDoubleSpinBox#InputBox,
QTextEdit#InputArea,
QPlainTextEdit#InputArea {
    background-color: #0F172A;
    border: 1px solid #334155;
    color: #E5E7EB;
}
QComboBox#InputBox::down-arrow {
    image: url("__COMBO_ARROW_LIGHT__");
}
QComboBox#InputBox QAbstractItemView {
    background-color: #0F172A;
    color: #E5E7EB;
    border: 1px solid #334155;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    outline: none;
}
QComboBox#InputBox:focus,
QLineEdit#InputBox:focus,
QDoubleSpinBox#InputBox:focus,
QTextEdit#InputArea:focus,
QPlainTextEdit#InputArea:focus {
    border: 1px solid #3B82F6;
}
QPushButton#PrimaryButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
}
QPushButton#PrimaryButton:hover {
    background-color: #1D4ED8;
}
QPushButton#SecondaryButton {
    background-color: #1E293B;
    color: #E5E7EB;
    border: 1px solid #334155;
}
QPushButton#SecondaryButton:hover {
    background-color: #334155;
}
QTableWidget {
    background-color: #0F172A;
    border: 1px solid #334155;
    color: #E5E7EB;
}
QSplitter::handle:vertical {
    background-color: #334155;
    margin: 2px 0;
}
QSplitter::handle:vertical:hover {
    background-color: #475569;
}
QSplitter::handle:horizontal {
    background-color: #334155;
    margin: 0 2px;
}
QSplitter::handle:horizontal:hover {
    background-color: #475569;
}
QHeaderView::section {
    background-color: #1E293B;
    color: #CBD5E1;
}
QTabWidget#ConfirmTabs::pane {
    background-color: #111827;
    border-color: #334155;
}
QTabWidget#ConfirmTabs QTabBar::tab {
    background-color: #0F172A;
    color: #94A3B8;
    border: 1px solid #334155;
    border-bottom: none;
}
QTabWidget#ConfirmTabs QTabBar::tab:selected {
    background-color: #111827;
    color: #E5E7EB;
}
QTabWidget#ConfirmTabs QTabBar::tab:hover {
    color: #E5E7EB;
}
"""

LIGHT_STYLESHEET = """
QWidget {
    background-color: #F3F6FB;
    color: #111827;
}
QLabel {
    background: transparent;
}
QMainWindow {
    background-color: #E8EDF5;
}
QFrame#Sidebar {
    background-color: #F8FAFC;
    border-right: 1px solid #D5DDE8;
}
QFrame#HeaderCard, QFrame#DashboardCard, QFrame#PlaceholderCard {
    background-color: #FFFFFF;
    border: 1px solid #D6DEE8;
    border-radius: 16px;
}
QFrame#DetailPanel {
    background-color: #FFFFFF;
    border: 1px solid #D6DEE8;
    border-radius: 14px;
}
QLabel#AppTitle,
QLabel#CardValue,
QLabel#SidebarTitle,
QLabel#PlaceholderTitle {
    color: #0F172A;
}
QLabel#AppSubtitle {
    color: #2563EB;
}
QLabel#MetaText,
QLabel#SidebarSubtitle,
QLabel#CardTitle,
QLabel#PlaceholderDescription {
    color: #475569;
}
QLabel#FieldLabel {
    color: #334155;
}
QLabel#MetaBadge {
    background-color: #EFF6FF;
    color: #1D4ED8;
    border: 1px solid #BFDBFE;
    border-radius: 10px;
    padding: 6px 10px;
}
QLabel#FeedbackLabel {
    color: #15803D;
}
QPushButton#NavButton,
QPushButton#ThemeToggleButton {
    border: none;
    background-color: transparent;
    color: #334155;
}
QPushButton#NavButton:hover,
QPushButton#ThemeToggleButton:hover {
    background-color: #E2E8F0;
}
QPushButton#NavButton:checked {
    background-color: #DBEAFE;
    color: #1D4ED8;
    font-weight: 600;
}
QComboBox#InputBox,
QLineEdit#InputBox,
QDoubleSpinBox#InputBox,
QTextEdit#InputArea,
QPlainTextEdit#InputArea {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    color: #111827;
}
QComboBox#InputBox::down-arrow {
    image: url("__COMBO_ARROW_DARK__");
}
QComboBox#InputBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #111827;
    border: 1px solid #CBD5E1;
    selection-background-color: #DBEAFE;
    selection-color: #1D4ED8;
    outline: none;
}
QComboBox#InputBox:focus,
QLineEdit#InputBox:focus,
QDoubleSpinBox#InputBox:focus,
QTextEdit#InputArea:focus,
QPlainTextEdit#InputArea:focus {
    border: 1px solid #2563EB;
}
QPushButton#PrimaryButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
}
QPushButton#PrimaryButton:hover {
    background-color: #1D4ED8;
}
QPushButton#SecondaryButton {
    background-color: #FFFFFF;
    color: #1F2937;
    border: 1px solid #CBD5E1;
}
QPushButton#SecondaryButton:hover {
    background-color: #F1F5F9;
}
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    color: #0F172A;
}
QSplitter::handle:vertical {
    background-color: #CBD5E1;
    margin: 2px 0;
}
QSplitter::handle:vertical:hover {
    background-color: #94A3B8;
}
QSplitter::handle:horizontal {
    background-color: #CBD5E1;
    margin: 0 2px;
}
QSplitter::handle:horizontal:hover {
    background-color: #94A3B8;
}
QHeaderView::section {
    background-color: #E2E8F0;
    color: #334155;
}
QTabWidget#ConfirmTabs::pane {
    background-color: #FFFFFF;
    border-color: #CBD5E1;
}
QTabWidget#ConfirmTabs QTabBar::tab {
    background-color: #F8FAFC;
    color: #64748B;
    border: 1px solid #CBD5E1;
    border-bottom: none;
}
QTabWidget#ConfirmTabs QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #0F172A;
}
QTabWidget#ConfirmTabs QTabBar::tab:hover {
    color: #1E293B;
}
"""


def get_stylesheet(theme: str) -> str:
    assets_dir = Path(__file__).resolve().parents[2] / "assets"
    combo_arrow_dark = (assets_dir / "combo_arrow_dark.svg").as_posix()
    combo_arrow_light = (assets_dir / "combo_arrow_light.svg").as_posix()
    if theme == "light":
        return (BASE_STYLESHEET + LIGHT_STYLESHEET).replace("__COMBO_ARROW_DARK__", combo_arrow_dark)
    return (BASE_STYLESHEET + DARK_STYLESHEET).replace("__COMBO_ARROW_LIGHT__", combo_arrow_light)
