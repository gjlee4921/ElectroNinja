# left_panel.py


import logging
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QToolButton, QTextEdit, 
    QPushButton, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from electroninja.config.settings import Config

logger = logging.getLogger('electroninja')

class LeftPanel(QFrame):
    """Left panel for ASC code editing"""
    
    toggleRequested = pyqtSignal(bool)
    imageGenerated = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.is_expanded = True
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
        is_checked = self.toggle_button.isChecked()
        self.is_expanded = is_checked
        self.toggleRequested.emit(is_checked)
        self.toggle_button.setArrowType(Qt.LeftArrow if is_checked else Qt.RightArrow)
        self.toggle_button.setText("Hide" if is_checked else "Show")
        
    def showCodeEditor(self):
        self.code_editor.show()
        
    def hideCodeEditor(self):
        self.code_editor.hide()
        
    def get_code(self):
        """Get the current code from the editor"""
        return self.code_editor.toPlainText()
        
    def set_code(self, code):
        """Set the code in the editor"""
        self.code_editor.setText(code)