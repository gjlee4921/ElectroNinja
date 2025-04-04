from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QScrollArea, QWidget, QSizePolicy, QLabel, QHBoxLayout
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from gui.chat_panel import ChatPanel
from gui.chat_input import ChatInputWidget

class RightPanel(QFrame):
    """
    The right-hand side panel displays:
      - A title ("Chat with ElectroNinja")
      - A scrollable chat panel for conversation
      - A chat input area for the user to type messages
    """
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
        # Note: No automatic welcome message is added

    def onSendMessage(self, text):
        if not text.strip():
            return
        self.chat_panel.add_message(text, is_user=True)
        self.chat_input.message_input.clear()
        self.messageSent.emit(text)

    def receive_message(self, message):
        # Display the assistant's message (from LLM) as a grey message
        QTimer.singleShot(50, lambda: self.chat_panel.add_message(message, is_user=False))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, lambda: self.chat_panel.resizeEvent(event))
