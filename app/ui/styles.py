BASE_STYLESHEET = """
QWidget {
    font-family: "PingFang SC", "Hiragino Sans GB", "Heiti SC";
    font-size: 13px;
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
QComboBox#InputBox,
QLineEdit#InputBox,
QTextEdit#InputArea {
    border-radius: 12px;
    padding: 10px 12px;
}
QTextEdit#InputArea {
    padding: 14px;
}
QScrollArea {
    border: none;
}
"""

DARK_STYLESHEET = """
QWidget {
    background-color: #111827;
    color: #E5E7EB;
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
QTextEdit#InputArea {
    background-color: #0F172A;
    border: 1px solid #334155;
    color: #E5E7EB;
}
QComboBox#InputBox:focus,
QLineEdit#InputBox:focus,
QTextEdit#InputArea:focus {
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
"""

LIGHT_STYLESHEET = """
QWidget {
    background-color: #F3F6FB;
    color: #111827;
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
QTextEdit#InputArea {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    color: #111827;
}
QComboBox#InputBox:focus,
QLineEdit#InputBox:focus,
QTextEdit#InputArea:focus {
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
"""


def get_stylesheet(theme: str) -> str:
    if theme == "light":
        return BASE_STYLESHEET + LIGHT_STYLESHEET
    return BASE_STYLESHEET + DARK_STYLESHEET
