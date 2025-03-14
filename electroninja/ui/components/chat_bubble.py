# chat_bubble.py


import logging
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QTextEdit, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QTextOption

logger = logging.getLogger('electroninja')

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
        
    def showEvent(self, event):
        """
        Once this bubble is actually shown in the UI,
        we schedule a second sizing pass to see the final layout width.
        """
        super().showEvent(event)
        QTimer.singleShot(0, self._delayedSizeAdjust)
        
    def _delayedSizeAdjust(self):
        """Called via QTimer once the bubble is actually displayed."""
        if not self.parent():
            return
            
        # 1) Measure the text's natural (unwrapped) width
        doc = self.message_text.document()
        doc.setTextWidth(999999)  # no wrapping
        natural_width = doc.size().width()
        
        # 2) Determine how much horizontal space is available
        parent_width = self.parent().width()
        available_width = parent_width - 20  # e.g., 20 px margin from edges
        
        # 3) We'll use the smaller of 'natural_width' or 'available_width'
        final_width = min(natural_width, available_width)
        
        # 4) Enforce a minimal width to avoid extremely skinny bubbles
        if final_width < 30:
            final_width = 30
            
        # 5) Call updateSize() to wrap the text at 'final_width'
        self.updateSize(final_width)
        
    def updateSize(self, max_width):
        """
        Fit the text within a maximum width, but allow short messages
        to use a narrower bubble. Also adds minimal vertical padding.
        """
        doc = self.message_text.document()
        
        # Step 1: Let the document measure its natural width (no wrapping yet).
        doc.setTextWidth(999999)
        natural_width = doc.size().width()
        
        # Step 2: Clamp the width between a minimum and max_width.
        min_width = 30
        final_width = min(natural_width, max_width)
        if final_width < min_width:
            final_width = min_width
            
        # Step 3: Apply wrapping at 'final_width' and measure height.
        doc.setTextWidth(final_width)
        doc_height = doc.size().height()
        
        # Step 4: Add a small vertical padding to avoid scrollbars.
        doc_height += 5
        
        # Step 5: Update the QTextEdit size.
        self.message_text.setFixedWidth(int(final_width))
        self.message_text.setFixedHeight(int(doc_height))
        
        # Step 6: Resize the outer QFrame (the bubble).
        self.adjustSize()