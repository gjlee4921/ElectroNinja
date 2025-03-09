# chat_panel.py

from PyQt5.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QFont

from electroninja.gui.chat_bubble import ChatBubble

class ChatPanel(QScrollArea):
    """
    A scrollable container for all chat bubbles (both user and assistant).
    Manages bubble widths to prioritize horizontal expansion.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bubbles = []
        self.bubble_containers = []
        self.initUI()
        
    def initUI(self):
        # Container widget for all chat bubbles
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background-color: #252526;")
        
        # Set size policy to allow expansion
        self.chat_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Vertical layout for the bubbles
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setSpacing(3)  # Reduced spacing between messages
        self.chat_layout.setContentsMargins(1, 1, 1, 1)  # Reduced margins
        self.chat_layout.setAlignment(Qt.AlignTop)

        # Add a stretch at the end so the bubbles "stick" to the top
        self.chat_layout.addStretch()

        # Configure the QScrollArea
        self.setWidget(self.chat_container)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("background-color: #252526; border: none;")

    def add_message(self, message, is_user=True):
        """
        Add a new bubble to the chat, either aligned left (assistant)
        or aligned right (user).
        """
        # Remove the final stretch temporarily
        if self.chat_layout.count() > 0:
            self.chat_layout.removeItem(self.chat_layout.itemAt(self.chat_layout.count() - 1))

        # Create a container for the bubble + horizontal layout
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # Calculate max bubble width as percentage of viewport
        viewport_width = self.viewport().width()
        # Allow more horizontal space - both message types should expand well horizontally
        # Machine messages can be wider than user messages
        max_width = int(viewport_width * (0.85 if is_user else 0.90))

        # Create the bubble
        bubble = ChatBubble(message, is_user, container)
        self.bubbles.append(bubble)
        self.bubble_containers.append(container)

        # Align the bubble: right for user, left for assistant
        if is_user:
            h_layout.addStretch(1)  # Push to the right
            h_layout.addWidget(bubble, 0, Qt.AlignRight)
        else:
            h_layout.addWidget(bubble, 0, Qt.AlignLeft)
            h_layout.addStretch(1)  # Push to the left

        # Set width limits and apply
        bubble.updateSize(max_width)
        
        # Force container to size properly to its contents
        container.adjustSize()
        
        # Add the container to the main chat layout
        self.chat_layout.addWidget(container)
        
        # Re-add the stretch at the bottom
        self.chat_layout.addStretch()

        # Use a small delay to ensure all layouts are updated before scrolling
        QTimer.singleShot(50, self.smooth_scroll_to_bottom)
        
        # Return the created bubble (useful for further manipulation)
        return bubble

    def smooth_scroll_to_bottom(self):
        """Smoothly scroll to the bottom of the chat."""
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
            # Already at the bottom, just ensure we're exactly at the max
            self.verticalScrollBar().setValue(max_pos)

    def resizeEvent(self, event):
        """
        When the chat panel is resized, update all bubbles to ensure proper width.
        This allows messages to expand or contract horizontally based on available space.
        """
        super().resizeEvent(event)
        viewport_width = self.viewport().width()
        
        # Update each bubble's width limits
        for i, bubble in enumerate(self.bubbles):
            # Calculate appropriate width (allow more horizontal space)
            if bubble.is_user:
                max_width = int(viewport_width * 0.85)
            else:
                max_width = int(viewport_width * 0.90)
                
            # Update the bubble size with new constraints
            bubble.updateSize(max_width)

    def clear_chat(self):
        """
        Remove all chat bubbles from the layout.
        """
        self.bubbles.clear()
        self.bubble_containers.clear()
        
        # Remove all widgets except the final stretch
        while self.chat_layout.count() > 1:
            item = self.chat_layout.itemAt(0)
            if item.widget():
                item.widget().deleteLater()
            self.chat_layout.removeItem(item)

        # Ensure we have that final stretch
        if self.chat_layout.count() == 0:
            self.chat_layout.addStretch()