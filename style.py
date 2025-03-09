# style.py

# Import Google fonts for use with QFontDatabase
IMPORT_FONTS = True  # Set to True to use custom fonts

# Define color palette - dark theme with purple accent
COLORS = {
    'background': '#1E1E1E',      # Main background
    'panel_bg': '#2F2F2F',        # Panel background
    'chat_bg': '#252526',         # Chat background (dark instead of white)
    'text_primary': '#FFFFFF',    # Primary text color
    'text_secondary': '#B0B0B0',  # Secondary text color
    'accent_purple': '#4B2F4C',   # Dark purple accent
    'accent_purple_light': '#5F3D61', # Light purple for hover states
    'border': '#3C3C3C',          # Border color
    'input_bg': '#2B2B2B',        # Input background
    'button_bg': '#4B2F4C',       # Button background (now purple)
    'button_hover': '#5F3D61'     # Button hover (lighter purple)
}

STYLE_SHEET = f"""
QMainWindow, QDialog {{
    background-color: {COLORS['background']};
}}

/* Rounded, darker frames */
QFrame {{
    background-color: {COLORS['panel_bg']};
    border-radius: 12px;
    border: 1px solid {COLORS['border']};
}}

/* Text labels */
QLabel {{
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', sans-serif;
}}

/* Text editors (code/chat) */
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

/* Scrollbars for TextEdit */
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

/* Single-line input */
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

/* General buttons */
QPushButton {{
    background-color: {COLORS['button_bg']};
    color: {COLORS['text_primary']};
    border-radius: 5px;
    border: none;
    padding: 10px 15px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 16px;
}}

/* Hover effect with a light purple accent */
QPushButton:hover {{
    background-color: {COLORS['button_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent_purple']};
}}

/* Tool buttons (toggle arrow) */
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

/* Circuit title styling */
#circuit_title {{
    font-family: 'Segoe UI', sans-serif;
    font-size: 40px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

/* Panel titles */
.panel_title {{
    font-family: 'Segoe UI', sans-serif;
    font-size: 20px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

/* Top bar styling */
#top_bar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                               stop:0 #8E44AD, stop:1 #9B59B6);
    border-radius: 12px;
    padding: 5px;
}}

/* Top bar title */
#app_title {{
    font-family: 'Segoe UI', sans-serif;
    font-size: 32px;
    font-weight: bold;
    color: white;
    padding: 5px;
}}

/* Button styling - using consistent colors */
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

/* Placeholder for circuit display */
#circuit_display {{
    background-color: {COLORS['input_bg']};
    color: {COLORS['text_secondary']};
    border: 2px dashed {COLORS['border']};
    border-radius: 10px;
    font-size: 20px;
}}
"""

def setup_fonts(app):
    """Setup custom fonts if IMPORT_FONTS is True"""
    if IMPORT_FONTS:
        from PyQt5.QtGui import QFontDatabase
        # You would add local font files here
        # Example: QFontDatabase.addApplicationFont("path/to/font.ttf")
        # For now we'll use system fonts that are likely to be available
        pass