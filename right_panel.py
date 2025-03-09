from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QScrollArea, QWidget, QSizePolicy,
    QLabel, QPushButton, QHBoxLayout, QTextEdit
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QTextCursor

class RightPanel(QFrame):
    """
    Right panel containing chat interface with fixed-position input area.
    """
    messageSent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        # Main layout for the entire panel
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

        # Stack layout to overlay elements
        self.stack_widget = QWidget()
        stack_layout = QVBoxLayout(self.stack_widget)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        stack_layout.setSpacing(0)
        main_layout.addWidget(self.stack_widget, 1)  # Give it all available space

        # Chat panel (will be sized to leave room for input area)
        self.chat_panel = ChatPanel(self)
        stack_layout.addWidget(self.chat_panel)
        
        # Fixed-position input area that sits at the bottom
        self.input_area = QWidget()
        self.input_area.setFixedHeight(60)  # Fixed height
        self.input_area.setStyleSheet("background: transparent; border: none;")
        
        # Horizontal layout for input and button
        input_layout = QHBoxLayout(self.input_area)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)  # Gap between input and button
        
        # Create the growing text input
        self.message_input = FixedBottomTextEdit()
        self.message_input.enterPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input, 1)  # Stretch to fill available width
        
        # Create the send button with fixed size and styling
        self.send_button = QPushButton("Send")
        self.send_button.setFixedSize(70, 38)  # Fixed width and height
        self.send_button.setObjectName("send_button")
        self.send_button.setStyleSheet("""
            background-color: #4B2F4C;
            color: #FFFFFF;
            border-radius: 8px;
            border: none;
            padding: 8px 12px;
            font-family: 'Segoe UI', sans-serif;
            font-size: 16px;
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        # Add the fixed input area to the main layout directly, not to the stack
        main_layout.addWidget(self.input_area)
        
        # Set bottom margin on chat panel to accommodate the input area height
        # This ensures chat messages don't go behind the input area
        self.chat_panel.setContentsMargins(0, 0, 0, 5)
        
        # Welcome message
        self.chat_panel.add_message("Welcome to ElectroNinja! How can I help you design your circuit today?", False)

    def send_message(self):
        """Send the message from the input field to the chat display."""
        text = self.message_input.toPlainText().strip()
        if text:
            # Show user message
            self.chat_panel.add_message(text, True)
            # Clear input
            self.message_input.clear()
            # Emit signal for main window
            self.messageSent.emit(text)

    def receive_message(self, message):
        """Add assistant message to chat."""
        self.chat_panel.add_message(message, False)


class FixedBottomTextEdit(QWidget):
    """
    A custom text edit that grows upward but keeps its bottom position fixed.
    Uses a more direct approach with a fixed-height container.
    """
    enterPressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up layout with no margins
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create a fixed container with QVBoxLayout that will push content up
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent; border: none;")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Create a spacer that will push the text edit to the bottom
        container_layout.addStretch(1)
        
        # Create the text edit
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(False)
        self.text_edit.setPlaceholderText("Type your message...")
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setStyleSheet("""
            background-color: #2B2B2B;
            color: #FFFFFF;
            border: 1px solid #3C3C3C;
            border-radius: 8px;
            font-family: 'Segoe UI', sans-serif;
            font-size: 16px;
            padding: 8px 12px;
        """)
        
        # Set initial fixed height for text edit
        self.text_edit.setFixedHeight(38)
        self.text_edit.setMinimumHeight(38)
        self.text_edit.setMaximumHeight(38)
        
        # Add the text edit to the container layout
        container_layout.addWidget(self.text_edit)
        
        # Add the container to the main layout
        self.layout.addWidget(self.container)
        
        # Connect signals
        self.text_edit.textChanged.connect(self.adjust_height)
        
        # Maximum height for multi-line text (approximately 5-6 lines)
        self.max_height = 150
        
    def adjust_height(self):
        """
        Adjust the height of the text edit based on content,
        but limit to max_height. Text edit grows upward by
        adjusting the text edit height but not the container.
        """
        # Reset to minimum to recalculate properly
        self.text_edit.setFixedHeight(38)
        
        # Get the document size with margins
        doc_height = self.text_edit.document().size().toSize().height() + 20  # Add margin
        
        # Set new height with limits
        new_height = min(max(38, doc_height), self.max_height)
        self.text_edit.setFixedHeight(new_height)
        
    def keyPressEvent(self, event):
        """Handle key press events, particularly Enter to send."""
        if self.text_edit.hasFocus():
            if event.key() == Qt.Key_Return and not event.modifiers():
                self.enterPressed.emit()
                return
        # Pass other events to parent
        super().keyPressEvent(event)
        
    def toPlainText(self):
        """Get the plain text content of the editor."""
        return self.text_edit.toPlainText()
        
    def clear(self):
        """Clear the text editor and reset its height."""
        self.text_edit.clear()
        self.text_edit.setFixedHeight(38)


class ChatBubble(QFrame):
    """Custom widget to display a chat message bubble that can expand fully."""
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
        # Container widget for all bubbles
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background-color: #252526;")
        
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setSpacing(15)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setAlignment(Qt.AlignTop)

        # Always keep a stretch at the end to push content up
        self.chat_layout.addStretch()

        # Configure the scroll area
        self.setWidget(self.chat_container)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("background-color: #252526; border: none;")

    def add_message(self, message, is_user=True):
        """Add a new bubble to the layout and scroll to the bottom smoothly."""
        # Remove the final stretch
        self.chat_layout.removeItem(self.chat_layout.itemAt(self.chat_layout.count()-1))
        
        bubble = ChatBubble(message, is_user, self.chat_container)
        # Align user messages to the right, assistant to the left
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
        # Ensure the stretch remains
        if self.chat_layout.count() == 0:
            self.chat_layout.addStretch()