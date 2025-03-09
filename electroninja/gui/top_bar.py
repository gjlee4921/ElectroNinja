# top_bar.py

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon, QFont

class TopBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("top_bar")
        self.initUI()

    def initUI(self):
        # Simple background with no borders or extras
        self.setStyleSheet("""
            background-color: #4B2F4C; 
            border-radius: 10px; 
            border: none;
        """)
        
        # Main layout with increased margins
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Center the title with stretchers
        layout.addStretch(1)
        
        # ElectroNinja title
        self.title = QLabel("ElectroNinja", self)
        
        # Use QFont directly with increased size and weight
        font = QFont("Segoe UI", 28)  # Slightly reduced font size
        font.setBold(True)
        font.setWeight(75)  # Explicitly set weight
        self.title.setFont(font)
        
        # More specific styling with z-order
        self.title.setStyleSheet("""
            color: white; 
            background: transparent; 
            padding: 2px; 
            margin: 0px;
        """)
        
        # Set alignment and size policy
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        # Add the title to the layout
        layout.addWidget(self.title)
        layout.addStretch(1)
        
        # Version label - slightly adjusted placement
        self.version_label = QLabel("v1.0", self)
        self.version_label.setStyleSheet("color: white; font-size: 14px; background: transparent;")
        self.version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.version_label)
        
        # Ensure enough height
        self.setMinimumHeight(80)
        self.setMaximumHeight(80)  # Fix the height to prevent layout shifts