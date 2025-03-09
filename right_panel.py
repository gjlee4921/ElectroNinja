from PyQt5.QtWidgets import QFrame, QVBoxLayout, QScrollArea, QWidget, QSizePolicy, QLabel
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QFont
from chat_input import ChatInputWidget

class RightPanel(QFrame):
    """
    Right panel containing the chat interface.
    """
    messageSent = pyqtSignal(str)

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

        # Chat messages area
        self.chat_panel = ChatPanel(self)
        self.chat_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.chat_panel, 1)

        # New chat input area using our custom widget
        self.chat_input = ChatInputWidget(max_lines=5, parent=self)
        self.chat_input.sendMessage.connect(self.onSendMessage)
        main_layout.addWidget(self.chat_input)

        # Welcome message
        self.chat_panel.add_message("Welcome to ElectroNinja! How can I help you design your circuit today?", False)

    def onSendMessage(self, text):
        # Add user message and emit signal for further processing
        self.chat_panel.add_message(text, True)
        self.messageSent.emit(text)

    def receive_message(self, message):
        """Add assistant message to chat."""
        self.chat_panel.add_message(message, False)

class ChatBubble(QFrame):
    """Custom widget to display a chat message bubble."""
    def __init__(self, message, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.initUI(message)

    def initUI(self, message):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Different background colors for user vs assistant
        if self.is_user:
            self.setStyleSheet("""
                background-color: #4B2F4C;
                border-radius: 6px;
                color: white;
                border: none;
            """)
            layout.setAlignment(Qt.AlignRight)
        else:
            self.setStyleSheet("""
                background-color: #333333;
                border-radius: 6px;
                color: white;
                border: none;
            """)
            layout.setAlignment(Qt.AlignLeft)
        
        # Label for the message text
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.message_label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.message_label)

        # Let the bubble expand as needed
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

class ChatPanel(QScrollArea):
    """Scrollable area that holds chat bubbles in a vertical layout."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        # Container widget for all chat bubbles
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background-color: #252526;")
        
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setSpacing(15)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setAlignment(Qt.AlignTop)

        # Add a stretch at the end to push content upward
        self.chat_layout.addStretch()

        # Configure the scroll area
        self.setWidget(self.chat_container)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("background-color: #252526; border: none;")

    def add_message(self, message, is_user=True):
        """Add a new chat bubble to the layout and scroll to the bottom smoothly."""
        # Remove the final stretch temporarily
        self.chat_layout.removeItem(self.chat_layout.itemAt(self.chat_layout.count()-1))
        
        bubble = ChatBubble(message, is_user, self.chat_container)
        align = Qt.AlignRight if is_user else Qt.AlignLeft
        self.chat_layout.addWidget(bubble, 0, align)

        # Re-add the stretch
        self.chat_layout.addStretch()
        
        # Smoothly scroll to the bottom
        self.smooth_scroll_to_bottom()

    def smooth_scroll_to_bottom(self):
        """Animate scrolling to the bottom of the chat."""
        current_pos = self.verticalScrollBar().value()
        max_pos = self.verticalScrollBar().maximum()
        if current_pos < max_pos:
            self.scroll_animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
            self.scroll_animation.setDuration(300)
            self.scroll_animation.setStartValue(current_pos)
            self.scroll_animation.setEndValue(max_pos)
            self.scroll_animation.setEasingCurve(QEasingCurve.OutCubic)
            self.scroll_animation.start()
        else:
            self.verticalScrollBar().setValue(max_pos)

    def clear_chat(self):
        """Remove all messages from the chat layout."""
        while self.chat_layout.count() > 1:  # keep the final stretch
            item = self.chat_layout.itemAt(0)
            if item.widget():
                item.widget().deleteLater()
            self.chat_layout.removeItem(item)
        if self.chat_layout.count() == 0:
            self.chat_layout.addStretch()
