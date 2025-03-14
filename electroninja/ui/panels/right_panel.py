#right_panel.py


import logging
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from electroninja.ui.components.chat_panel import ChatPanel
from electroninja.ui.components.chat_input import ChatInputWidget

logger = logging.getLogger('electroninja')

class RightPanel(QFrame):
    """Right panel for chat interface"""
    
    messageSent = pyqtSignal(str)  # Emitted when the user sends a new message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Panel title
        self.chat_title = QLabel("Chat with ElectroNinja", self)
        self.chat_title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: white; letter-spacing: 0.5px;"
        )
        self.chat_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.chat_title)
        
        # Chat messages area (scrollable)
        self.chat_panel = ChatPanel(self)
        self.chat_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.chat_panel, stretch=1)
        
        # Chat input area
        self.chat_input = ChatInputWidget(max_lines=5, parent=self)
        self.chat_input.sendMessage.connect(self.onSendMessage)
        main_layout.addWidget(self.chat_input)
        
    def onSendMessage(self, text):
        """Handle a new message from the user"""
        if not text.strip():
            return
            
        # Add message to chat panel
        self.chat_panel.add_message(text, is_user=True)
        
        # Clear input
        self.chat_input.message_input.clear()
        
        # Emit signal to notify parent
        self.messageSent.emit(text)
        
    def receive_message(self, message):
        """Display a message from the assistant"""
        logger.info(f"Receiving message in chat panel: {message[:50]}...")
        
        # Use a small delay to ensure smooth UI updates
        QTimer.singleShot(50, lambda: self.chat_panel.add_message(message, is_user=False))
        
    def clear_chat(self):
        """Clear all chat messages"""
        self.chat_panel.clear_chat()