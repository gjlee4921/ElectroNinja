# middle_panel.py

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QSizePolicy,
    QHBoxLayout, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class MiddlePanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        # Main layout for the middle panel
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        # Header with "Current Circuit" title - no wrapper, just text
        self.circuit_title = QLabel("Current Circuit", self)
        self.circuit_title.setStyleSheet("font-size: 36px; font-weight: bold; color: white; letter-spacing: 1px; background: transparent;")
        self.circuit_title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.circuit_title)

        # Container for the square display with center alignment
        self.display_container = QWidget()
        display_layout = QVBoxLayout(self.display_container)
        display_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add horizontal layout to center the square
        h_layout = QHBoxLayout()
        h_layout.setAlignment(Qt.AlignCenter)  # Center the frame horizontally
        
        # The frame that will be kept square
        self.display_frame = QFrame()
        self.display_frame.setStyleSheet("""
            background-color: #2B2B2B;
            border: 1px dashed #5A5A5A;
            border-radius: 5px;
        """)
        
        # Start with a reasonable size
        self.display_frame.setMinimumSize(400, 400)
        
        # Layout for the placeholder text
        frame_layout = QVBoxLayout(self.display_frame)
        frame_layout.setAlignment(Qt.AlignCenter)  # Center the text vertically
        
        # Placeholder text
        self.circuit_display = QLabel("Circuit Screenshot Placeholder")
        self.circuit_display.setAlignment(Qt.AlignCenter)
        self.circuit_display.setStyleSheet("border: none; color: #AAAAAA;")
        self.circuit_display.setFont(QFont("Segoe UI", 16))
        self.circuit_display.setWordWrap(True)
        
        frame_layout.addWidget(self.circuit_display)
        h_layout.addWidget(self.display_frame)
        display_layout.addLayout(h_layout)
        
        # Add to main layout
        self.main_layout.addWidget(self.display_container)
        
        # "Edit with LT Spice" button
        buttons_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit with LT Spice", self)
        self.edit_button.setObjectName("edit_button")
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addStretch()
        
        self.main_layout.addLayout(buttons_layout)
        
        # Add a stretcher at the bottom
        self.main_layout.addStretch()
        
        # Connect resize event
        self.resizeEvent = self.on_resize
    
    def on_resize(self, event):
        """Handle resize to maintain square display frame"""
        # Call the parent's resize event handler
        super().resizeEvent(event)
        
        # Calculate the square size based on available space
        # Account for margins and other UI elements
        available_width = self.width() - 100  # Account for left/right margins
        available_height = self.height() - 200  # Account for title, button, and margins
        
        # Use the smaller dimension to determine square size
        square_size = min(available_width, available_height)
        
        # Only set if we have a positive size
        if square_size > 0:
            self.display_frame.setFixedSize(square_size, square_size)