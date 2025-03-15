# middle_panel.py

import os
import logging
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QSizePolicy,
    QHBoxLayout, QWidget, QMessageBox, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QFont, QPixmap
from electroninja.config.settings import Config

logger = logging.getLogger('electroninja')

class MiddlePanel(QFrame):
    """Middle panel for circuit visualization"""
    
    editRequested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.current_image_path = None
        self.transition_duration = 500  # Animation duration in ms
        self.initUI()
        
    def initUI(self):
        # Main layout for the middle panel
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)
        
        # Header with "Current Circuit" title
        self.circuit_title = QLabel("Current Circuit", self)
        self.circuit_title.setStyleSheet(
            "font-size: 36px; font-weight: bold; color: white; letter-spacing: 1px; background: transparent;"
        )
        self.circuit_title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.circuit_title)
        
        # Container for the square display with center alignment
        self.display_container = QWidget()
        display_layout = QVBoxLayout(self.display_container)
        display_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add horizontal layout to center the square
        h_layout = QHBoxLayout()
        h_layout.setAlignment(Qt.AlignCenter)
        
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
        frame_layout.setAlignment(Qt.AlignCenter)
        
        # Placeholder text
        self.circuit_display = QLabel("Circuit Screenshot Placeholder")
        self.circuit_display.setAlignment(Qt.AlignCenter)
        self.circuit_display.setStyleSheet("border: none; color: #AAAAAA;")
        self.circuit_display.setFont(QFont("Segoe UI", 16))
        self.circuit_display.setWordWrap(True)
        
        # An image label that will actually show the PNG
        self.image_label = QLabel(self.display_frame)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: none; color: #AAAAAA;")
        
        # Add opacity effect for fade transitions
        self.opacity_effect = QGraphicsOpacityEffect(self.image_label)
        self.opacity_effect.setOpacity(1.0)
        self.image_label.setGraphicsEffect(self.opacity_effect)
        
        # Create opacity animation
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(self.transition_duration)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        frame_layout.addWidget(self.image_label)
        frame_layout.addWidget(self.circuit_display)
        h_layout.addWidget(self.display_frame)
        display_layout.addLayout(h_layout)
        
        # Add to main layout
        self.main_layout.addWidget(self.display_container)
        
        # "Edit with LT Spice" button
        buttons_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit with LT Spice", self)
        self.edit_button.setObjectName("edit_button")
        self.edit_button.clicked.connect(self.on_edit_clicked)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addStretch()
        
        self.main_layout.addLayout(buttons_layout)
        
        # Add a stretcher at the bottom
        self.main_layout.addStretch()
        
    def set_circuit_image(self, image_path):
        """
        Update the image display with a new circuit image using fade transition
        
        Args:
            image_path (str): Path to the image file
        """
        logger.info(f"Setting circuit image: {image_path}")
        
        # Validate the image path
        if not os.path.exists(image_path):
            logger.error(f"Image file does not exist: {image_path}")
            return
            
        # Keep track of the new image path
        new_image_path = image_path
        
        # Skip if this is the same image we're already displaying
        if self.current_image_path and os.path.normpath(self.current_image_path) == os.path.normpath(new_image_path):
            logger.info(f"Image is already displayed, skipping transition: {new_image_path}")
            return
        
        # If there's no current image, just set it directly
        if not self.current_image_path:
            self._set_image_direct(new_image_path)
            return
            
        # Fade out the current image
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        
        # Disconnect any previous connections to avoid multiple callbacks
        try:
            self.fade_animation.finished.disconnect()
        except TypeError:
            # No connections exist
            pass
        
        # Set up the callback to change the image when fade out is complete
        def fade_out_complete():
            # Set the new image
            self._set_image_direct(new_image_path)
            
            # Fade in the new image
            fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
            fade_in.setDuration(self.transition_duration)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.InOutCubic)
            fade_in.start()
            
        # Connect the finished signal to our callback
        self.fade_animation.finished.connect(fade_out_complete)
        
        # Start the fade out animation
        self.fade_animation.start()
        
    def _set_image_direct(self, image_path):
        """
        Set the image directly without animation
        
        Args:
            image_path (str): Path to the image file
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file does not exist for direct setting: {image_path}")
            return
            
        self.current_image_path = image_path
        
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            logger.error(f"Failed to load image: {image_path}")
            self.image_label.setText("Failed to load image")
            self.circuit_display.setText("Circuit Screenshot Placeholder")
        else:
            # Hide placeholder text, show the image
            self.circuit_display.setText("")
            
            # Determine appropriate size for the image
            available_width = self.display_frame.width()
            available_height = self.display_frame.height()
            
            self.image_label.setPixmap(pixmap.scaled(
                available_width, 
                available_height, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            ))
            
    def on_edit_clicked(self):
        """Request to edit the circuit in LTSpice"""
        self.editRequested.emit()
        
    def resizeEvent(self, event):
        """Handle resize to maintain square display frame"""
        super().resizeEvent(event)
        
        # Calculate the square size based on available space
        available_width = self.width() - 100
        available_height = self.height() - 200
        square_size = min(available_width, available_height)
        
        if square_size > 0:
            self.display_frame.setFixedSize(square_size, square_size)
            
            # If an image is set, rescale it
            if self.current_image_path and os.path.exists(self.current_image_path):
                pixmap = QPixmap(self.current_image_path)
                if not pixmap.isNull():
                    self.image_label.setPixmap(pixmap.scaled(
                        square_size, 
                        square_size, 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    ))