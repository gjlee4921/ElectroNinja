from PyQt5.QtWidgets import QWidget, QTextEdit, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, Qt, QEvent
from PyQt5.QtGui import QFontMetrics

class AutoResizingTextEdit(QTextEdit):
    def __init__(self, max_lines=5, min_height=40, parent=None):
        """
        min_height: should match the send button height.
        max_lines: maximum number of lines to expand to before scrolling.
        """
        super().__init__(parent)
        self.max_lines = max_lines
        self.min_height = min_height
        # Set a small document margin for better measurement
        self.document().setDocumentMargin(2)
        self.textChanged.connect(self.updateHeight)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.updateHeight()

    def updateHeight(self):
        # Compute the desired height from the document size
        doc_height = self.document().documentLayout().documentSize().height()
        fm = self.fontMetrics()
        line_height = fm.lineSpacing()
        max_height = line_height * self.max_lines + 10  # 10px for padding
        new_height = doc_height + 10  # add padding
        if new_height < self.min_height:
            new_height = self.min_height
        if new_height > max_height:
            new_height = max_height
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFixedHeight(int(new_height))

class ChatInputWidget(QWidget):
    sendMessage = pyqtSignal(str)

    def __init__(self, max_lines=5, parent=None):
        super().__init__(parent)
        self.max_lines = max_lines
        self.initUI()

    def initUI(self):
        # Instead of fixing the height for the entire widget,
        # we only set a minimum height equal to the send button's height.
        self.setMinimumHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignBottom)

        # Create a container to hold the text edit and force it to be bottom-aligned.
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        text_layout.setAlignment(Qt.AlignBottom)
        # No stretch added here so that the container shrinks to the text edit.

        # Here we set min_height=40 to match the send button's height.
        self.message_input = AutoResizingTextEdit(
            max_lines=self.max_lines,
            min_height=40  # Matches the send button's fixed height
        )
        self.message_input.setPlaceholderText("Type your message...")
        text_layout.addWidget(self.message_input, alignment=Qt.AlignBottom)

        layout.addWidget(text_container, 1)

        # Create the send button with fixed dimensions (70x40) so it matches the text edit.
        self.send_button = QPushButton("Send", self)
        self.send_button.setFixedSize(70, 40)
        layout.addWidget(self.send_button, 0, alignment=Qt.AlignBottom)

        # Connect the button and enter key to sending the message.
        self.send_button.clicked.connect(self.onSendClicked)
        self.message_input.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.message_input and event.type() == QEvent.KeyPress:
            # Allow Shift+Enter to insert a newline; plain Enter triggers send.
            if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
                self.onSendClicked()
                return True
        return super().eventFilter(obj, event)

    def onSendClicked(self):
        text = self.message_input.toPlainText().strip()
        if text:
            self.sendMessage.emit(text)
            self.message_input.clear()
