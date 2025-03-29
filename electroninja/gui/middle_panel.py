from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QSizePolicy,
    QHBoxLayout, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

ltspice_path = r"C:\Users\leegj\AppData\Local\Programs\ADI\LTspice\LTspice.exe"

class MiddlePanel(QFrame):
    """
    The MiddlePanel shows the final circuit image in a square area
    and provides a button to manually open LTSpice and process the circuit.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        # Main layout for the middle panel
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        # Header with "Current Circuit" title
        self.circuit_title = QLabel("Current Circuit", self)
        self.circuit_title.setStyleSheet(
            "font-size: 36px; font-weight: bold; color: white; letter-spacing: 1px; background: transparent;"
        )
        self.circuit_title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.circuit_title)

        # Container for the square display with center alignment
        self.display_container = QWidget()
        display_layout = QVBoxLayout(self.display_container)
        display_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add horizontal layout to center the square
        h_layout = QHBoxLayout()
        h_layout.setAlignment(Qt.AlignCenter)
        
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
        frame_layout.setAlignment(Qt.AlignCenter)
        
        # Placeholder text
        self.circuit_display = QLabel("Circuit Screenshot Placeholder")
        self.circuit_display.setAlignment(Qt.AlignCenter)
        self.circuit_display.setStyleSheet("border: none; color: #AAAAAA;")
        self.circuit_display.setFont(QFont("Segoe UI", 16))
        self.circuit_display.setWordWrap(True)

        # An image label that will actually show the PNG
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
        """Handle resize to maintain square display frame."""
        super().resizeEvent(event)
        
        # Calculate the square size based on available space
        available_width = self.width() - 100
        available_height = self.height() - 200
        square_size = min(available_width, available_height)
        
        if square_size > 0:
            self.display_frame.setFixedSize(square_size, square_size)
    
    def set_circuit_image(self, image_path: str):
        """Update the image display with a new circuit image."""
        print("Setting middle panel circuit image to the new one...")
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.image_label.setText("Failed to load image")
            self.circuit_display.setText("Circuit Screenshot Placeholder")
        else:
            # Hide placeholder text, show the image
            self.circuit_display.setText("")
            self.image_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def edit_with_ltspice(self):
        """
        Manually open the circuit from the main window's left panel in LTSpice
        and then show the resulting image in the middle panel.
        """
        import os
        import time
        import pygetwindow as gw
        import pyautogui
        import subprocess
        from electroninja.circuits.circuit_saver import circuit_saver
        from PyQt5.QtWidgets import QMessageBox

        # The real left panel is in the main window
        main_window = self.window()
        left_panel = main_window.left_panel

        circuit_text = left_panel.code_editor.toPlainText().strip()
        if not circuit_text:
            QMessageBox.warning(self, "Error", "No circuit code entered!")
            return

        # Save the .asc file as a temporary file
        temp_file_path = os.path.join(os.getcwd(), "ltspice_edit.asc")
        with open(temp_file_path, "w") as f:
            f.write(circuit_text)

        print(f"🔹 Temporary LTSpice file saved at: {temp_file_path}")

        # Try opening LTSpice
        try:
            ltspice_process = subprocess.Popen([ltspice_path, temp_file_path])
        except FileNotFoundError:
            QMessageBox.critical(self, "LTSpice Error", "LTSpice executable not found!")
            return

        print("🔹 LTSpice opened. Monitoring for exit...")

        # Monitor for "Save changes?" pop-up
        initial_len = len(gw.getWindowsWithTitle("LTspice"))
        while ltspice_process.poll() is None:
            time.sleep(0.5)
            windows = gw.getWindowsWithTitle("LTspice")
            print(windows)
            if len(windows) > 1:
                print("🔹 Detected LTSpice save pop-up. Pressing 'Cancel'...")
                time.sleep(0.5)
                pyautogui.press("esc")
                break
        
        # Now process the schematic (with new_window=False)
        asc_path, img_path = circuit_saver(temp_file_path, new_window=False)

        # Update the left panel with the newest ASC code
        if asc_path and os.path.exists(asc_path):
            with open(asc_path, "r") as f:
                updated_circuit_text = f.read()
            left_panel.code_editor.setText(updated_circuit_text)
            print("✅ Updated LeftPanel with the latest circuit file.")

        # Update this middle panel with the final PNG
        if img_path and os.path.exists(img_path):
            self.set_circuit_image(img_path)

        # Clean up
        try:
            os.remove(temp_file_path)
            print(f"🗑️ Deleted temporary LTSpice file: {temp_file_path}")
        except Exception as e:
            print(f"⚠️ Error deleting temporary file: {e}")
