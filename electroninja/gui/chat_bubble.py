# chat_bubble.py

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QTextEdit, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QTextOption

class ChatBubble(QFrame):
    """
    A single chat message "bubble" that prioritizes horizontal expansion
    before wrapping text and growing vertically.
    """
    def __init__(self, message, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.message = message
        self.initUI(message)

    def initUI(self, message):
        # Very minimal margins to reduce height
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(0)
        
        # Set size policies to prevent expansion beyond necessary size
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        # Different background colors for user vs. assistant
        if self.is_user:
            self.setStyleSheet("""
                background-color: #4B2F4C;
                border-radius: 6px;
                color: white;
                border: none;
            """)
        else:
            self.setStyleSheet("""
                background-color: #333333;
                border-radius: 6px;
                color: white;
                border: none;
            """)

        # Use QTextEdit with minimal settings for optimal sizing
        self.message_text = QTextEdit(self)
        self.message_text.setPlainText(message)
        self.message_text.setReadOnly(True)
        
        # Remove all extra UI elements and set minimal styling
        self.message_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_text.setFrameStyle(QFrame.NoFrame)
        self.message_text.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.message_text.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        
        # Set minimal document margin to reduce extra space
        self.message_text.document().setDocumentMargin(1)
        
        # Ultra-minimal styling
        self.message_text.setStyleSheet("""
            background-color: transparent;
            color: white;
            border: none;
            padding: 0px;
            margin: 0px;
        """)
        
        # Set size policy to prevent vertical expansion
        self.message_text.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # Set font
        self.message_text.setFont(QFont("Segoe UI", 12))
        
        # Add the text edit to the layout
        layout.addWidget(self.message_text)
    
    def updateSize(self, max_width):
        """
        Update the size of the bubble based on content and maximum width.
        Prioritizes horizontal expansion before growing vertically.
        Ensures short messages don't take up unnecessary width.
        """
        # Calculate the ideal width based on text content
        doc = self.message_text.document()
        
        # First check what width the text would naturally need
        doc.setTextWidth(-1)  # Reset any previous text width
        natural_width = doc.idealWidth() + 10  # Add small padding
        
        # Set minimum width to ensure very short messages look good
        min_width = 80
        
        # For short messages, use their natural width (but no less than min_width)
        # For longer messages, cap at max_width
        target_width = int(min(max(natural_width, min_width), max_width))
        
        # Apply the determined width
        self.message_text.setFixedWidth(target_width)
        
        # Force the document to lay out the text with this width
        doc.setTextWidth(target_width)
        
        # Calculate the document height after layout - get exact height
        doc_height = doc.size().height()
        
        # Set the text edit height to exactly fit its content without extra space
        self.message_text.setFixedHeight(int(doc_height))
        
        # Adjust the layout margins to be minimal
        layout = self.layout()
        layout.setContentsMargins(6, 4, 6, 4)
        
        # Adjust the bubble's size to fit the text exactly
        self.adjustSize()