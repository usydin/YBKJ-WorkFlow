APP_STYLESHEET = """
QWidget {
    background-color: #111827;
    color: #E5E7EB;
    font-family: "PingFang SC", "Hiragino Sans GB", "Heiti SC", sans-serif;
    font-size: 13px;
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
    font-size: 22px;
    font-weight: 700;
    color: #F9FAFB;
}
QLabel#AppSubtitle {
    font-size: 13px;
    color: #93C5FD;
}
QLabel#MetaText {
    color: #9CA3AF;
}
QLabel#SidebarTitle {
    font-size: 16px;
    font-weight: 700;
}
QLabel#SidebarSubtitle {
    color: #9CA3AF;
}
QPushButton#NavButton {
    text-align: left;
    padding: 10px 14px;
    border-radius: 10px;
    border: none;
    background-color: transparent;
    color: #D1D5DB;
}
QPushButton#NavButton:hover {
    background-color: #1E293B;
}
QPushButton#NavButton:checked {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 600;
}
QLabel#CardValue {
    font-size: 28px;
    font-weight: 700;
    color: #F9FAFB;
}
QLabel#CardTitle {
    font-size: 13px;
    color: #9CA3AF;
}
QLabel#PlaceholderTitle {
    font-size: 18px;
    font-weight: 700;
}
QLabel#PlaceholderDescription {
    color: #9CA3AF;
    line-height: 1.5;
}
QScrollArea {
    border: none;
}
"""
