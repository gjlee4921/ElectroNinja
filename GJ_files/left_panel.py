import os
import tempfile
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QToolButton, QTextEdit, 
    QPushButton, QHBoxLayout, QSplitter, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

class LeftPanel(QFrame):
    toggleRequested = pyqtSignal(bool)
    imageGenerated = pyqtSignal(str) 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_expanded = True
        self.initUI()
        
    def initUI(self):
        self.setMinimumWidth(80)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header layout
        header_layout = QHBoxLayout()
        
        self.asc_title = QLabel(".asc File", self)
        self.asc_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        self.asc_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_layout.addWidget(self.asc_title)
        
        header_layout.addStretch()
        
        # Toggle button
        self.toggle_button = QToolButton(self)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.LeftArrow)
        self.toggle_button.setText("Hide")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.clicked.connect(self.on_toggle_clicked)
        header_layout.addWidget(self.toggle_button)
        
        main_layout.addLayout(header_layout)

        # Code editor
        self.code_editor = QTextEdit(self)
        self.code_editor.setPlaceholderText("Enter .asc code here...")
        self.code_editor.setFont(QFont("Consolas", 13))
        main_layout.addWidget(self.code_editor)

        # Compile button
        self.compile_button = QPushButton("Compile Circuit", self)
        self.compile_button.setObjectName("compile_button")
        self.compile_button.clicked.connect(self.compile_and_save_circuit)  # Connect function
        main_layout.addWidget(self.compile_button)

    def compile_and_save_circuit(self):
        """Handles compiling, saving, passing to circuit_saver, and cleanup."""
        circuit_text = self.code_editor.toPlainText().strip()
        if not circuit_text:
            print("No circuit code entered.")
            return

        # Create a temporary file in the current directory
        with tempfile.NamedTemporaryFile(delete=False, suffix=".asc", mode="w", dir=os.getcwd()) as temp_file:
            temp_file.write(circuit_text)
            temp_file_path = temp_file.name  # Store the file path

        print(f"Temporary file created: {temp_file_path}")

        from electroninja.circuits.circuit_saver import circuit_saver
        _, img = circuit_saver(temp_file_path)

        self.imageGenerated.emit(img)

        # Delete the temporary file after usage
        try:
            os.remove(temp_file_path)
            print(f"Temporary file deleted: {temp_file_path}")
        except Exception as e:
            print(f"Error deleting temp file: {e}")

    def on_toggle_clicked(self):
        is_checked = self.toggle_button.isChecked()
        self.is_expanded = is_checked
        self.toggleRequested.emit(is_checked)
        self.toggle_button.setArrowType(Qt.LeftArrow if is_checked else Qt.RightArrow)
        self.toggle_button.setText("Hide" if is_checked else "Show")
