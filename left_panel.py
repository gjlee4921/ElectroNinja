from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QToolButton, QTextEdit, 
    QPushButton, QHBoxLayout, QSplitter, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

class LeftPanel(QFrame):
    toggleRequested = pyqtSignal(bool)
    """
    Emitted when the toggle button is clicked.
    True means 'expand', False means 'collapse'.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_expanded = True  # Track panel expansion state
        self.initUI()

    def initUI(self):
        # Width will be controlled from MainWindow
        # We don't set a fixed width here as it will be managed by the parent
        
        # Set a minimum width for when collapsed
        self.setMinimumWidth(80)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header with title and toggle button
        header_layout = QHBoxLayout()
        
        # Title for .asc file - simplified, no wrapper
        self.asc_title = QLabel(".asc File", self)
        self.asc_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; letter-spacing: 0.5px; background: transparent;")
        self.asc_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_layout.addWidget(self.asc_title)
        
        header_layout.addStretch()
        
        # Toggle button (arrow + text)
        self.toggle_button = QToolButton(self)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.LeftArrow)
        self.toggle_button.setText("Hide")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.clicked.connect(self.on_toggle_clicked)
        header_layout.addWidget(self.toggle_button)
        
        main_layout.addLayout(header_layout)

        # Code editor for .asc with syntax highlighting
        self.code_editor = QTextEdit(self)
        self.code_editor.setPlaceholderText("Enter .asc code here...")
        
        # Set a monospace font for code
        code_font = QFont("Consolas", 13)
        code_font.setStyleHint(QFont.Monospace)
        self.code_editor.setFont(code_font)
        
        main_layout.addWidget(self.code_editor)

        # Compile button - now purple to match design
        self.compile_button = QPushButton("Compile Circuit", self)
        self.compile_button.setObjectName("compile_button")
        # You can add an icon if you have one
        # self.compile_button.setIcon(QIcon("path/to/compile_icon.png"))
        main_layout.addWidget(self.compile_button)

    def on_toggle_clicked(self):
        # When the toggle button is clicked, emit the signal with isChecked()
        # isChecked() == True => we want to expand
        is_checked = self.toggle_button.isChecked()
        
        # Store the state so mainWindow can check it
        self.is_expanded = is_checked
        
        # Emit signal to trigger animation in main window
        self.toggleRequested.emit(is_checked)
        
        # Update the arrow and text
        if is_checked:
            self.toggle_button.setArrowType(Qt.LeftArrow)
            self.toggle_button.setText("Hide")
        else:
            self.toggle_button.setArrowType(Qt.RightArrow)
            self.toggle_button.setText("Show")

    def showCodeEditor(self):
        """Show the code editor components without changing width"""
        self.code_editor.show()
        self.compile_button.show()
        self.asc_title.show()
        self.toggle_button.setArrowType(Qt.LeftArrow)
        self.toggle_button.setText("Hide")
        
        # Don't set fixed width here, let animation handle it

    def hideCodeEditor(self):
        self.code_editor.hide()
        self.compile_button.hide()
        self.asc_title.hide()
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.setText("Show")