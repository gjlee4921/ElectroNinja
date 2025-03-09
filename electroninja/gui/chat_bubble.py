from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QTextEdit, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextOption

class ChatBubble(QFrame):
    """
    A single chat message "bubble" that is only as tall as it needs 
    to display the text, plus a small padding to avoid scrollbars.
    """
    def __init__(self, message, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.message = message
        self.initUI(message)

    def initUI(self, message):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(0)

        # Bubble background color
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

        # QTextEdit for displaying the message
        self.message_text = QTextEdit(self)
        self.message_text.setPlainText(message)
        self.message_text.setReadOnly(True)
        
        # No scrollbars so the bubble grows vertically
        self.message_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_text.setFrameStyle(QFrame.NoFrame)
        self.message_text.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.message_text.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.message_text.document().setDocumentMargin(1)

        # Minimal styling
        self.message_text.setStyleSheet("""
            background-color: transparent;
            color: white;
            border: none;
            padding: 0px;
            margin: 0px;
        """)
        self.message_text.setFont(QFont("Segoe UI", 12))

        # We'll manually set width & height in updateSize
        self.message_text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout.addWidget(self.message_text)

    def updateSize(self, max_width):
        """
        Fit the text within max_width, then compute the exact height 
        and add a small padding (e.g. +10) to prevent scrollbars.
        """
        doc = self.message_text.document()

        # Wrap text at max_width
        doc.setTextWidth(max_width)

        # Fix the text edit width
        self.message_text.setFixedWidth(max_width)

        # Ensure layout is up-to-date
        # doc.size() calculates the required height
        doc_height = doc.size().height()

        # Add a small padding to ensure no scrollbars appear
        doc_height += 15

        self.message_text.setFixedHeight(int(doc_height))

        # Adjust the bubble's size
        self.adjustSize()
