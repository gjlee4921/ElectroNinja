# left_panel.py

import logging
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QTextEdit, QHBoxLayout,
    QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor
from electroninja.config.settings import Config

logger = logging.getLogger('electroninja')

class LeftPanel(QFrame):
    """Left panel for ASC code editing"""
    
    # Signals
    toggleRequested = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation_timer = None
        self.animation_text = ""
        self.animation_position = 0
        self.animation_speed = 5  # Characters per tick
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components"""
        self.setMinimumWidth(80)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Header with title and toggle button
        header_layout = QHBoxLayout()
        
        # ASC file title
        self.asc_title = QLabel(".asc File", self)
        self.asc_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        self.asc_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_layout.addWidget(self.asc_title)
        
        header_layout.addStretch()
        
        self.main_layout.addLayout(header_layout)
        
        # Code editor
        self.code_editor = QTextEdit(self)
        self.code_editor.setPlaceholderText("Enter .asc code here...")
        self.code_editor.setFont(QFont("Consolas", 13))
        self.main_layout.addWidget(self.code_editor)
        
        # Add compile button
        self.compile_button = QPushButton("Compile Code", self)
        self.compile_button.setObjectName("compile_button")  # Set object name to match CSS selector in styles.py
        
        # Apply the same font styling as the ASC title label
        font = self.asc_title.font()
        self.compile_button.setFont(font)
        
        # Make text bold like the title
        self.compile_button.setStyleSheet("font-weight: bold;")
        
        self.main_layout.addWidget(self.compile_button)
        
    def on_toggle_clicked(self):
        """Handle toggle button click"""
        self.is_expanded = self.toggle_button.isChecked()
        self.toggleRequested.emit(self.is_expanded)
        self.toggle_button.setArrowType(Qt.LeftArrow if self.is_expanded else Qt.RightArrow)
        self.toggle_button.setText("Hide" if self.is_expanded else "Show")
        
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
        """Set the code in the editor with optional animation"""
        if not animated:
            self.code_editor.setText(code)
            self.code_editor.moveCursor(QTextCursor.Start)
            return
            
        # Setup for animated insertion
        self.animation_text = code
        self.animation_position = 0
        self.code_editor.clear()
        
        # Stop any existing animation
        if self.animation_timer:
            self.animation_timer.stop()
            
        # Start new animation
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animate_text)
        self.animation_timer.start(10)  # Update every 10ms
        
    def _animate_text(self):
        """Insert text incrementally for animation effect"""
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
        """Clear the code editor and reset iteration display"""
        if self.animation_timer:
            self.animation_timer.stop()
            
        self.code_editor.clear()
        self.iteration_label.hide()
        
    def is_animating(self):
        """Check if animation is in progress"""
        return self.animation_timer is not None and self.animation_timer.isActive()
