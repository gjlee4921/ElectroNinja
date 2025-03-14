# top_bar.py

import logging
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

logger = logging.getLogger('electroninja')

class TopBar(QFrame):
    """Top bar with application title"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("top_bar")
        self.initUI()
        
    def initUI(self):
        # Styling
        self.setStyleSheet("""
            background-color: #4B2F4C; 
            border-radius: 10px; 
            border: none;
        """)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Center the title with stretchers
        layout.addStretch(1)
        
        # ElectroNinja title
        self.title = QLabel("ElectroNinja", self)
        
        # Set font
        font = QFont("Segoe UI", 28)
        font.setBold(True)
        font.setWeight(75)
        self.title.setFont(font)
        
        # Styling
        self.title.setStyleSheet("""
            color: white; 
            background: transparent; 
            padding: 2px; 
            margin: 0px;
        """)
        
        # Alignment
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        # Add to layout
        layout.addWidget(self.title)
        layout.addStretch(1)
        
        # Version label
        self.version_label = QLabel("v1.0", self)
        self.version_label.setStyleSheet("color: white; font-size: 14px; background: transparent;")
        self.version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.version_label)
        
        # Size constraints
        self.setMinimumHeight(80)
        self.setMaximumHeight(80)