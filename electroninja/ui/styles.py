"""Styling for the ElectroNinja application"""

# Define color palette - dark theme with purple accent
COLORS = {
    'background': '#1E1E1E',           # Main background
    'panel_bg': '#2F2F2F',             # Panel background
    'chat_bg': '#252526',              # Chat background (dark instead of white)
    'text_primary': '#FFFFFF',         # Primary text color
    'text_secondary': '#B0B0B0',       # Secondary text color
    'accent_purple': '#4B2F4C',        # Dark purple accent
    'accent_purple_light': '#5F3D61',  # Light purple for hover states
    'border': '#3C3C3C',               # Border color
    'input_bg': '#2B2B2B',             # Input background
    'button_bg': '#4B2F4C',            # Button background (now purple)
    'button_hover': '#5F3D61'          # Button hover (lighter purple)
}

STYLE_SHEET = f"""
/* Main Window and Dialog Backgrounds */
QMainWindow, QDialog {{
    background-color: {COLORS['background']};
}}

/* Panels and Frames */
QFrame {{
    background-color: {COLORS['panel_bg']};
    border-radius: 12px;
    border: 1px solid {COLORS['border']};
}}

/* Labels */
QLabel {{
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', sans-serif;
}}

/* Multi-line Text Editors */
QTextEdit {{
    background-color: {COLORS['input_bg']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    font-family: 'Consolas', monospace;
    font-size: 16px;
    padding: 8px;
    selection-background-color: {COLORS['accent_purple']}80; /* 50% opacity */
}}

/* Scrollbar styling for QTextEdit */
QTextEdit QScrollBar:vertical {{
    background-color: {COLORS['input_bg']};
    width: 12px;
    border-radius: 6px;
}}
QTextEdit QScrollBar::handle:vertical {{
    background-color: {COLORS['accent_purple']};
    border-radius: 6px;
    min-height: 20px;
}}
QTextEdit QScrollBar::add-line:vertical,
QTextEdit QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Single-line Text Input */
QLineEdit {{
    background-color: {COLORS['input_bg']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 16px;
    padding: 8px 12px;
    selection-background-color: {COLORS['accent_purple']}80;
}}

/* General Button Styling */
QPushButton {{
    background-color: {COLORS['button_bg']};
    color: {COLORS['text_primary']};
    border-radius: 5px;
    border: none;
    padding: 10px 15px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 16px;
}}
QPushButton:hover {{
    background-color: {COLORS['button_hover']};
}}
QPushButton:pressed {{
    background-color: {COLORS['accent_purple']};
}}
QPushButton:disabled {{
    background-color: gray;
    color: {COLORS['text_secondary']};
}}

/* Tool Buttons (e.g., toggle arrows) */
QToolButton {{
    background-color: {COLORS['accent_purple']};
    color: {COLORS['text_primary']};
    border-radius: 8px;
    border: none;
    padding: 10px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 16px;
}}
QToolButton:hover {{
    background-color: {COLORS['accent_purple_light']};
}}
QToolButton:pressed {{
    background-color: #7D3C98;
}}

/* Circuit Title Styling */
#circuit_title {{
    font-family: 'Segoe UI', sans-serif;
    font-size: 40px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

/* Panel Title Styling */
.panel_title {{
    font-family: 'Segoe UI', sans-serif;
    font-size: 20px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

/* Top Bar Styling */
#top_bar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8E44AD, stop:1 #9B59B6);
    border-radius: 12px;
    padding: 5px;
}}
#app_title {{
    font-family: 'Segoe UI', sans-serif;
    font-size: 32px;
    font-weight: bold;
    color: white;
    padding: 5px;
}}

/* Specific Button Stylings */
#compile_button {{
    background-color: {COLORS['button_bg']};
}}
#compile_button:hover {{
    background-color: {COLORS['button_hover']};
}}
#edit_button {{
    background-color: {COLORS['button_bg']};
    font-size: 18px;
    padding: 10px 20px;
}}
#edit_button:hover {{
    background-color: {COLORS['button_hover']};
}}
#send_button {{
    background-color: {COLORS['accent_purple']};
    border-radius: 8px;
}}

/* Circuit Display Placeholder */
#circuit_display {{
    background-color: {COLORS['input_bg']};
    color: {COLORS['text_secondary']};
    border: 2px dashed {COLORS['border']};
    border-radius: 10px;
    font-size: 20px;
}}
"""

def setup_fonts(app):
    """Setup custom fonts if needed."""
    from PyQt5.QtGui import QFontDatabase
    # Add local font files here if desired.
    pass
