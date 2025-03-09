# right_panel.py

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QScrollArea, QWidget, QSizePolicy, QLabel,
    QHBoxLayout
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

# Import our custom components
from electroninja.gui.chat_panel import ChatPanel
from electroninja.gui.chat_input import ChatInputWidget


class RightPanel(QFrame):
    """
    The right-hand side panel, containing:
      - A title ("Chat with ElectroNinja")
      - A scrollable chat panel
      - A chat input area
    """
    messageSent = pyqtSignal(str)  # Emitted when the user sends a new message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        # Main vertical layout for this QFrame
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

        # Add welcome message after a short delay to ensure UI is ready
        QTimer.singleShot(100, self.add_welcome_message)

    def add_welcome_message(self):
        """Add welcome message once UI is ready."""
        self.chat_panel.add_message(
            "Welcome to ElectroNinja! How can I help you design your circuit today?",
            is_user=False
        )

    def onSendMessage(self, text):
        """
        Triggered when the user presses the send button or hits Enter.
        """
        # Only process non-empty messages
        if not text.strip():
            return
            
        # 1. Add user's message to the chat panel
        self.chat_panel.add_message(text, is_user=True)
        
        # 2. Clear the input field
        self.chat_input.message_input.clear()
        
        # 3. Emit a signal so the rest of the app can respond
        self.messageSent.emit(text)

    def receive_message(self, message):
        """
        Call this method to display an assistant (machine) message.
        """
        # Use a short delay to make the conversation feel more natural
        # and to ensure UI updates properly
        QTimer.singleShot(50, lambda: self.chat_panel.add_message(message, is_user=False))
        
    def resizeEvent(self, event):
        """Handle panel resize events."""
        super().resizeEvent(event)
        # Ensure chat panel gets updated properly when the panel is resized
        QTimer.singleShot(0, lambda: self.chat_panel.resizeEvent(event))