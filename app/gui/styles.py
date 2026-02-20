"""
Global stylesheet for GrowHire GUI.
Modern, clean theme with professional accent colors.
"""

# Color palette
COLORS = {
    "bg_main": "#f5f6f8",
    "bg_card": "#ffffff",
    "bg_input": "#ffffff",
    "border": "#e1e4e8",
    "border_focus": "#0a66c2",
    "text": "#1a1a1a",
    "text_secondary": "#5c5c5c",
    "accent": "#0a66c2",
    "accent_hover": "#004182",
    "accent_light": "#e8f0fe",
    "success": "#057642",
    "success_bg": "#e6f4ea",
    "warning": "#b34d00",
    "warning_bg": "#fef3e6",
    "danger": "#c5221f",
    "danger_bg": "#fce8e6",
    "shadow": "rgba(0, 0, 0, 0.08)",
}

# Font family - system UI for native feel
FONT_FAMILY = "Segoe UI, SF Pro Display, system-ui, sans-serif"
FONT_SIZE_BASE = 13
FONT_SIZE_SMALL = 11
FONT_SIZE_TITLE = 15


def get_stylesheet() -> str:
    """Returns the global application stylesheet."""
    return f"""
    /* Main window */
    QWidget {{
        background-color: {COLORS["bg_main"]};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_BASE}px;
        color: {COLORS["text"]};
    }}

    /* Group boxes - card style */
    QGroupBox {{
        background-color: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 10px;
        margin-top: 14px;
        padding: 18px 18px 12px 18px;
        font-weight: 600;
        font-size: {FONT_SIZE_TITLE}px;
        color: {COLORS["text"]};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 16px;
        top: 4px;
        padding: 2px 12px;
        background-color: {COLORS["bg_card"]};
        color: {COLORS["accent"]};
        border-radius: 6px;
        font-weight: 600;
    }}

    /* Buttons - primary */
    QPushButton {{
        background-color: {COLORS["accent"]};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: {FONT_SIZE_BASE}px;
        min-height: 20px;
    }}

    QPushButton:hover {{
        background-color: {COLORS["accent_hover"]};
    }}

    QPushButton:pressed {{
        background-color: #003b6f;
    }}

    QPushButton:disabled {{
        background-color: #a0a0a0;
        color: #e0e0e0;
    }}

    /* Line edits */
    QLineEdit {{
        background-color: {COLORS["bg_input"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 10px 14px;
        font-size: {FONT_SIZE_BASE}px;
        color: {COLORS["text"]};
        selection-background-color: {COLORS["accent_light"]};
    }}

    QLineEdit:focus {{
        border: 1px solid {COLORS["border_focus"]};
    }}

    QLineEdit::placeholder {{
        color: #9ca3af;
    }}

    /* Combo boxes */
    QComboBox {{
        background-color: {COLORS["bg_input"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 10px 14px;
        padding-right: 32px;
        font-size: {FONT_SIZE_BASE}px;
        color: {COLORS["text"]};
        min-height: 20px;
    }}

    QComboBox:hover {{
        border: 1px solid {COLORS["border_focus"]};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 28px;
        background: transparent;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {COLORS["text_secondary"]};
        margin-right: 10px;
        width: 0;
        height: 0;
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 4px;
        selection-background-color: {COLORS["accent_light"]};
    }}

    /* Checkboxes */
    QCheckBox {{
        spacing: 10px;
        font-size: {FONT_SIZE_BASE}px;
        color: {COLORS["text"]};
    }}

    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border: 2px solid {COLORS["border"]};
        border-radius: 4px;
        background-color: white;
    }}

    QCheckBox::indicator:checked {{
        background-color: {COLORS["accent"]};
        border-color: {COLORS["accent"]};
    }}

    QCheckBox::indicator:hover {{
        border-color: {COLORS["accent"]};
    }}

    /* Labels */
    QLabel {{
        color: {COLORS["text"]};
        font-size: {FONT_SIZE_BASE}px;
    }}

    /* Scroll bars */
    QScrollBar:vertical {{
        background: {COLORS["bg_main"]};
        width: 10px;
        border-radius: 5px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: #c0c0c0;
        border-radius: 5px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: #a0a0a0;
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* Tables */
    QTableWidget {{
        background-color: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 10px;
        gridline-color: {COLORS["border"]};
        font-size: {FONT_SIZE_BASE}px;
    }}

    QTableWidget::item {{
        padding: 8px;
        color: {COLORS["text"]};
    }}

    QHeaderView::section {{
        background-color: {COLORS["accent_light"]};
        color: {COLORS["accent"]};
        padding: 12px 8px;
        border: none;
        border-bottom: 2px solid {COLORS["border"]};
        font-weight: 600;
    }}

    /* Dialogs */
    QDialog {{
        background-color: {COLORS["bg_main"]};
    }}

    /* Text edit (read-only content) */
    QTextEdit {{
        background-color: #fafafa;
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 10px;
        font-size: {FONT_SIZE_BASE}px;
        color: {COLORS["text"]};
    }}
    """


def get_header_style() -> str:
    """Returns inline style for header/title labels."""
    return f"""
        font-size: 22px;
        font-weight: 700;
        color: {COLORS["text"]};
        padding: 8px 0;
        letter-spacing: -0.5px;
    """
