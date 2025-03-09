# middle_panel.py
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QSizePolicy,
    QHBoxLayout, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from electroninja.gui.left_panel import LeftPanel

ltspice_path = r"C:\Users\leegj\AppData\Local\Programs\ADI\LTspice\LTspice.exe"

class MiddlePanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        # Main layout for the middle panel
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        self.left_panel = LeftPanel(self)

        # Header with "Current Circuit" title - no wrapper, just text
        self.circuit_title = QLabel("Current Circuit", self)
        self.circuit_title.setStyleSheet("font-size: 36px; font-weight: bold; color: white; letter-spacing: 1px; background: transparent;")
        self.circuit_title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.circuit_title)

        # Container for the square display with center alignment
        self.display_container = QWidget()
        display_layout = QVBoxLayout(self.display_container)
        display_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add horizontal layout to center the square
        h_layout = QHBoxLayout()
        h_layout.setAlignment(Qt.AlignCenter)  # Center the frame horizontally
        
        # The frame that will be kept square
        self.display_frame = QFrame()
        self.display_frame.setStyleSheet("""
            background-color: #2B2B2B;
            border: 1px dashed #5A5A5A;
            border-radius: 5px;
        """)
        
        # Start with a reasonable size
        self.display_frame.setMinimumSize(400, 400)
        
        # Layout for the placeholder text
        frame_layout = QVBoxLayout(self.display_frame)
        frame_layout.setAlignment(Qt.AlignCenter)  # Center the text vertically
        
        # Placeholder text
        self.circuit_display = QLabel("Circuit Screenshot Placeholder")
        self.circuit_display.setAlignment(Qt.AlignCenter)
        self.circuit_display.setStyleSheet("border: none; color: #AAAAAA;")
        self.circuit_display.setFont(QFont("Segoe UI", 16))
        self.circuit_display.setWordWrap(True)

        # Define self.image_label so it exists before set_circuit_image()
        self.image_label = QLabel(self.display_frame)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: none; color: #AAAAAA;")
        frame_layout.addWidget(self.image_label)
        
        frame_layout.addWidget(self.circuit_display)
        h_layout.addWidget(self.display_frame)
        display_layout.addLayout(h_layout)
        
        # Add to main layout
        self.main_layout.addWidget(self.display_container)
        
        # "Edit with LT Spice" button
        buttons_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit with LT Spice", self)
        self.edit_button.setObjectName("edit_button")
        self.edit_button.clicked.connect(self.edit_with_ltspice)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addStretch()
        
        self.main_layout.addLayout(buttons_layout)
        
        # Add a stretcher at the bottom
        self.main_layout.addStretch()
        
        # Connect resize event
        self.resizeEvent = self.on_resize
    
    def on_resize(self, event):
        """Handle resize to maintain square display frame"""
        # Call the parent's resize event handler
        super().resizeEvent(event)
        
        # Calculate the square size based on available space
        # Account for margins and other UI elements
        available_width = self.width() - 100  # Account for left/right margins
        available_height = self.height() - 200  # Account for title, button, and margins
        
        # Use the smaller dimension to determine square size
        square_size = min(available_width, available_height)
        
        # Only set if we have a positive size
        if square_size > 0:
            self.display_frame.setFixedSize(square_size, square_size)
    
    def set_circuit_image(self, image_path):
        """Update the image display with a new circuit image."""
        print("Setting middle panel circuit image to the new one...")
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.image_label.setText("Failed to load image")
        else:
            self.image_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def edit_with_ltspice(self):

        """Open LTSpice, auto-cancel save, and display processed schematic."""
        import os
        import time
        import pygetwindow as gw
        import pyautogui
        import subprocess
        from electroninja.circuits.circuit_saver import circuit_saver

        left_panel = self.window().left_panel
        circuit_text = left_panel.code_editor.toPlainText().strip()
        
        if not circuit_text:
            QMessageBox.warning(self, "Error", "No circuit code entered!")
            return

        # ✅ Save the .asc file as a temporary file
        temp_file_path = os.path.join(os.getcwd(), "ltspice_edit.asc")
        with open(temp_file_path, "w") as f:
            f.write(circuit_text)

        print(f"🔹 Temporary LTSpice file saved at: {temp_file_path}")

        # ✅ Open LTSpice with the saved .asc file

        try:
            ltspice_process = subprocess.Popen([ltspice_path, temp_file_path])
        except FileNotFoundError:
            QMessageBox.critical(self, "LTSpice Error", "LTSpice executable not found!")
            return

        print("🔹 LTSpice opened. Monitoring for exit...")

        # ✅ Monitor and cancel "Save changes?" prompt
        while ltspice_process.poll() is None:
            time.sleep(0.5)
            windows = gw.getWindowsWithTitle("LTspice")
            if len(windows)>1:
                print("🔹 Detected LTSpice save pop-up. Pressing 'Cancel'...")
                time.sleep(0.5)
                pyautogui.press("esc")  # Press "Cancel"
                break
        


        # ✅ Process the schematic without opening a new window
        asc_path, img_path = circuit_saver(temp_file_path, new_window = False)

        if os.path.exists(asc_path):
            with open(asc_path, "r") as f:
                updated_circuit_text = f.read()
            left_panel.code_editor.setText(updated_circuit_text)  # ✅ Overwrite the LeftPanel text
            print("✅ Updated LeftPanel with the latest circuit file.")

        if img_path:
            self.set_circuit_image(img_path)

        # ✅ Delete temporary .asc file
        try:
            os.remove(temp_file_path)
            print(f"🗑️ Deleted temporary LTSpice file: {temp_file_path}")
        except Exception as e:
            print(f"⚠️ Error deleting temporary file: {e}")
