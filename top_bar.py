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
        self.setStyleSheet("background-color: #4B2F4C; border-radius: 10px; border: none;")
        
        # Main layout with plenty of space
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)  # More vertical space to prevent text cutoff
        
        # Center the title with stretchers
        layout.addStretch(1)
        
        # ElectroNinja title - WHITE text
        self.title = QLabel("ElectroNinja", self)
        
        # Direct styling instead of using stylesheet
        font = QFont("Segoe UI", 30)
        font.setBold(True)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1)
        self.title.setFont(font)
        self.title.setStyleSheet("color: white; background: transparent; padding: 0px;")
        
        layout.addWidget(self.title)
        layout.addStretch(1)
        
        # Version label
        self.version_label = QLabel("v1.0", self)
        self.version_label.setStyleSheet("color: white; font-size: 14px; background: transparent;")
        layout.addWidget(self.version_label)
        
        # Increased height to ensure text fits
        self.setFixedHeight(80)