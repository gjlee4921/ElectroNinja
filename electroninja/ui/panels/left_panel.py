# left_panel.py

import logging
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QToolButton, QTextEdit, 
    QPushButton, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor
from electroninja.config.settings import Config

logger = logging.getLogger('electroninja')

class LeftPanel(QFrame):
    """Left panel for ASC code editing"""
    
    # Signals
    toggleRequested = pyqtSignal(bool)
    imageGenerated = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.is_expanded = True
        self.animation_timer = None  # Timer for animating text insertion
        self.animation_text = ""     # Text to be animated
        self.animation_position = 0  # Current position in the animation
        self.animation_speed = 5     # Characters per timer tick (higher = faster)
        self.initUI()
        
    def initUI(self):
        self.setMinimumWidth(80)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header layout
        header_layout = QHBoxLayout()
        
        self.asc_title = QLabel(".asc File", self)
        self.asc_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        self.asc_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_layout.addWidget(self.asc_title)
        
        header_layout.addStretch()
        
        # Toggle button
        self.toggle_button = QToolButton(self)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.LeftArrow)
        self.toggle_button.setText("Hide")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.clicked.connect(self.on_toggle_clicked)
        header_layout.addWidget(self.toggle_button)
        
        main_layout.addLayout(header_layout)
        
        # Code editor
        self.code_editor = QTextEdit(self)
        self.code_editor.setPlaceholderText("Enter .asc code here...")
        self.code_editor.setFont(QFont("Consolas", 13))
        main_layout.addWidget(self.code_editor)
        
        # Compile button
        self.compile_button = QPushButton("Compile Circuit", self)
        self.compile_button.setObjectName("compile_button")
        main_layout.addWidget(self.compile_button)
        
    def on_toggle_clicked(self):
        """Handle toggle button click"""
        is_checked = self.toggle_button.isChecked()
        self.is_expanded = is_checked
        self.toggleRequested.emit(is_checked)
        self.toggle_button.setArrowType(Qt.LeftArrow if is_checked else Qt.RightArrow)
        self.toggle_button.setText("Hide" if is_checked else "Show")
        
    def showCodeEditor(self):
        """Show the code editor"""
        self.code_editor.show()
        
    def hideCodeEditor(self):
        """Hide the code editor"""
        self.code_editor.hide()
        
    def get_code(self):
        """Get the current code from the editor"""
        return self.code_editor.toPlainText()
        
    def set_code(self, code, animated=False):
        """
        Set the code in the editor
        
        Args:
            code (str): The code to set
            animated (bool): Whether to animate the text insertion
        """
        if not animated:
            # Set code immediately
            self.code_editor.setText(code)
            self.code_editor.moveCursor(QTextCursor.Start)
            return
            
        # Set up animation
        self.animation_text = code
        self.animation_position = 0
        
        # Clear editor before starting animation
        self.code_editor.clear()
        
        # Stop any existing animation
        if self.animation_timer:
            self.animation_timer.stop()
            
        # Create animation timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animate_text)
        self.animation_timer.start(10)  # Update every 10ms
        
    def _animate_text(self):
        """Animate the text insertion"""
        # Check if animation is complete
        if self.animation_position >= len(self.animation_text):
            self.animation_timer.stop()
            return
            
        # Calculate how many characters to insert
        chars_to_insert = min(self.animation_speed, len(self.animation_text) - self.animation_position)
        
        # Insert the next chunk of text
        next_text = self.animation_text[self.animation_position:self.animation_position + chars_to_insert]
        self.code_editor.insertPlainText(next_text)
        
        # Update position
        self.animation_position += chars_to_insert
        
        # Ensure text is visible
        cursor = self.code_editor.textCursor()
        self.code_editor.setTextCursor(cursor)
        self.code_editor.ensureCursorVisible()
        
    def clear_code(self):
        """Clear the code editor"""
        # Stop any active animation
        if self.animation_timer:
            self.animation_timer.stop()
            
        self.code_editor.clear()
        
    def is_animating(self):
        """Check if animation is in progress"""
        return self.animation_timer is not None and self.animation_timer.isActive()