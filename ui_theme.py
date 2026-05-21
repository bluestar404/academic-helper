"""Application-wide Qt stylesheet."""

APP_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #f0f2f8;
}
QGroupBox {
    font-weight: 600;
    font-size: 13px;
    color: #1a2a4a;
    border: 1px solid #c8d0e0;
    border-radius: 8px;
    margin-top: 12px;
    padding: 14px 10px 10px 10px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QLineEdit, QSpinBox, QComboBox, QPlainTextEdit, QTableWidget {
    border: 1px solid #c5cedd;
    border-radius: 6px;
    padding: 6px 8px;
    background: #fafbff;
    color: #1e293b;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {
    border: 1px solid #3b6fd9;
}
QPushButton {
    background-color: #e8edf7;
    color: #1a2a4a;
    border: 1px solid #b8c4dc;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #d6e0f5;
}
QPushButton:pressed {
    background-color: #c5d4f0;
}
QPushButton#primaryBtn {
    background-color: #2563eb;
    color: white;
    border: none;
    font-weight: 600;
}
QPushButton#primaryBtn:hover {
    background-color: #1d4ed8;
}
QPushButton#previewBtn {
    background-color: #0d9488;
    color: white;
    border: none;
}
QPushButton#previewBtn:hover {
    background-color: #0f766e;
}
QTabWidget::pane {
    border: 1px solid #c8d0e0;
    border-radius: 6px;
    background: #ffffff;
    top: -1px;
}
QTabBar::tab {
    background: #e8edf7;
    color: #334155;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #1d4ed8;
    font-weight: 600;
}
QTableWidget {
    gridline-color: #e2e8f0;
    alternate-background-color: #f8fafc;
}
QHeaderView::section {
    background-color: #e8edf7;
    color: #1a2a4a;
    padding: 6px;
    border: none;
    font-weight: 600;
}
QStatusBar {
    background: #e8edf7;
    color: #475569;
}
QListWidget {
    border: 1px solid #c5cedd;
    border-radius: 6px;
    background: #fafbff;
}
QListWidget::item {
    padding: 10px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #dbeafe;
    color: #1e3a8a;
}
QLabel#totalMarks {
    font-size: 15px;
    font-weight: 600;
    color: #1d4ed8;
}
"""
