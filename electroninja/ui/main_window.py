# electroninja/ui/main_window.py

import logging
import os
import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QApplication, QPushButton
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSlot, QTimer
from electroninja.config.settings import Config
from electroninja.utils.async_workers import ElectroNinjaWorker
from electroninja.utils.error_handler import handle_error
from electroninja.utils.file_operations import save_file
from electroninja.ui.panels.left_panel import LeftPanel
from electroninja.ui.panels.middle_panel import MiddlePanel
from electroninja.ui.panels.right_panel import RightPanel
from electroninja.ui.components.top_bar import TopBar
from electroninja.ui.styles import STYLE_SHEET, setup_fonts

logger = logging.getLogger('electroninja')

class MainWindow(QMainWindow):
    """Main application window for ElectroNinja"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ElectroNinja - Electrical Engineer Agent")
        self.setGeometry(100, 50, 1400, 800)
        
        # Initialize configuration
        self.config = Config()
        
        # Panel widths
        self.left_panel_collapsed_width = 80
        self.left_panel_expanded_width = 300
        
        # Current file path
        self.current_circuit_file = None
        
        # Current prompt tracking
        self.current_prompt_id = 1
        
        # Processing state
        self.is_processing = False
        
        # Current worker thread
        self.worker = None
        
        # Initialize UI
        self.init_ui()
        self.connect_signals()
        self.adjust_panel_widths()
        
        # Initial panel state - expanded
        self.left_panel.is_expanded = True
        
    def init_ui(self):
        """Initialize the UI components"""
        # Set up fonts
        setup_fonts(QApplication.instance())
        
        # Apply stylesheet
        self.setStyleSheet(STYLE_SHEET)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Add top bar
        self.top_bar = TopBar(self)
        main_layout.addWidget(self.top_bar)
        
        # Create panels layout
        self.panels_layout = QHBoxLayout()
        self.panels_layout.setSpacing(10)
        main_layout.addLayout(self.panels_layout)
        
        # Create panels
        self.left_panel = LeftPanel(self)
        self.middle_panel = MiddlePanel(self)
        self.right_panel = RightPanel(self)
        
        # Configure left panel
        self.left_panel.setMinimumWidth(self.left_panel_collapsed_width)
        self.left_panel.setMaximumWidth(self.left_panel_expanded_width)
        
        # Add panels to layout
        self.panels_layout.addWidget(self.left_panel)
        self.panels_layout.addWidget(self.middle_panel)
        self.panels_layout.addWidget(self.right_panel)
        
        logger.info("UI initialized")
        
    def connect_signals(self):
        """Connect signals between components"""
        # Left panel signals
        self.left_panel.toggleRequested.connect(self.on_left_panel_toggle)
        self.left_panel.compile_button.clicked.connect(self.compile_circuit)
        
        # Middle panel signals
        self.middle_panel.editRequested.connect(self.edit_with_ltspice)
        
        # Right panel signals
        self.right_panel.messageSent.connect(self.handle_message)
        
        logger.info("Signals connected")
    
    def on_left_panel_toggle(self, is_expanding):
        """Handle left panel toggle button click"""
        logger.info(f"Left panel toggle: {'expand' if is_expanding else 'collapse'}")
        
        if is_expanding:
            current_width = self.left_panel.width()
            self.left_panel.showCodeEditor()
            self.animate_left_panel(current_width, self.left_panel_expanded_width)
        else:
            current_width = self.left_panel.width()
            self.animate_left_panel(current_width, self.left_panel_collapsed_width)
            self.left_panel.hideCodeEditor()
            
    def animate_left_panel(self, start_width, end_width):
        """Animate the left panel width change"""
        animation = QPropertyAnimation(self.left_panel, b"maximumWidth")
        animation.setDuration(600)
        animation.setStartValue(start_width)
        animation.setEndValue(end_width)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        
    def adjust_panel_widths(self):
        """Adjust panel widths based on window size"""
        total_width = self.width() - 40
        left_width = int(total_width * 0.22)
        right_width = int(total_width * 0.28)
        
        self.left_panel_expanded_width = left_width
        
        if self.left_panel.is_expanded:
            self.left_panel.setMaximumWidth(left_width)
        else:
            self.left_panel.setMaximumWidth(self.left_panel_collapsed_width)
            
        self.right_panel.setFixedWidth(right_width)
        
        logger.info(f"Adjusted panel widths: Left={left_width}, Right={right_width}")
        
    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        self.adjust_panel_widths()
        
    @pyqtSlot(str)
    def handle_message(self, message):
        """Handle incoming chat messages"""
        logger.info(f"Handling message: {message[:50]}...")
        
        # Ignore if already processing
        if self.is_processing:
            logger.info("Ignoring message - already processing")
            self.right_panel.receive_message("I'm still working on your previous request. Please wait...")
            return
            
        # Set processing state
        self.is_processing = True
        self.right_panel.set_processing(True)
        
        # Ensure left panel is expanded to show the code
        if not self.left_panel.is_expanded:
            self.on_left_panel_toggle(True)
        
        # Process the request
        self.process_request(message)
    
    def process_request(self, request):
        """Process a user request"""
        logger.info(f"Processing request: {request}")
        
        # Clear any existing code and image
        self.left_panel.clear_code()
        
        # Create worker thread for processing
        self.worker = ElectroNinjaWorker(request, self.current_prompt_id)
        
        # Connect signals
        self.worker.chatResponseGenerated.connect(self.right_panel.receive_message)
        self.worker.ascCodeGenerated.connect(self.on_asc_code_generated)
        self.worker.imageGenerated.connect(self.middle_panel.set_circuit_image)
        self.worker.resultReady.connect(self.handle_result)
        
        # Increment prompt ID for next request
        self.current_prompt_id += 1
        
        # Start processing
        self.worker.start()
        
    def on_asc_code_generated(self, asc_code):
        """
        Handle ASC code generation with animation
        
        Args:
            asc_code (str): Generated ASC code
        """
        # Skip empty or non-circuit responses
        if not asc_code or asc_code == "N":
            return
            
        # Add version marker if missing
        if not asc_code.startswith("Version 4"):
            asc_code = "Version 4\nSHEET 1 880 680\n" + asc_code
            
        # Set the code with animation (always show what we have)
        self.left_panel.set_code(asc_code, animated=True)
        
        # We don't save to current.asc anymore - only use output0/code.asc

    def handle_result(self, result):
        """Handle processing result"""
        try:
            if result.get("success", False):
                # Success message
                if result.get("final_status", ""):
                    self.right_panel.receive_message(
                        f"Circuit processing complete: {result['final_status']}"
                    )
            else:
                # Handle failure
                if "error" in result:
                    self.right_panel.receive_message(
                        f"Error processing circuit: {result['error']}"
                    )
                elif result.get("final_status", ""):
                    self.right_panel.receive_message(result["final_status"])
                else:
                    self.right_panel.receive_message(
                        "I was unable to verify the circuit design. The best attempt is shown."
                    )
        finally:
            # Reset processing state
            self.is_processing = False
            self.right_panel.set_processing(False)
            
    def compile_circuit(self):
        """Manually compile the current circuit"""
        logger.info("Manual circuit compilation requested")
        
        # Get code from editor
        asc_code = self.left_panel.get_code()
        
        if not asc_code.strip():
            QMessageBox.warning(self, "Error", "Please enter circuit code first!")
            return
            
        # Process circuit
        self.right_panel.receive_message("Processing circuit...")
        
        # Create a worker to compile the circuit
        compile_worker = ElectroNinjaWorker(
            "COMPILE:" + asc_code, 
            self.current_prompt_id,
            compile_only=True
        )
        
        # Connect signals
        compile_worker.imageGenerated.connect(self.middle_panel.set_circuit_image)
        compile_worker.resultReady.connect(self.handle_compile_result)
        
        # Increment prompt ID
        self.current_prompt_id += 1
        
        # Start processing
        compile_worker.start()
            
    def handle_compile_result(self, result):
        """Handle compilation result"""
        if result.get("success", False):
            self.right_panel.receive_message("Circuit compiled successfully!")
        else:
            self.right_panel.receive_message(f"Error: {result.get('error', 'Failed to compile circuit')}")
            
    def edit_with_ltspice(self):
        """Edit circuit in LTSpice"""
        logger.info("Edit with LTSpice requested")
        
        # Get code from editor
        asc_code = self.left_panel.get_code()
        
        if not asc_code.strip():
            QMessageBox.warning(self, "Error", "Please enter circuit code first!")
            return
            
        try:
            # Set processing state
            self.is_processing = True
            self.right_panel.set_processing(True)
            
            # Process circuit with LTSpice
            self.right_panel.receive_message("Opening circuit in LTSpice. Make your changes and save...")
            
            # Create a worker to edit the circuit
            edit_worker = ElectroNinjaWorker(
                "EDIT:" + asc_code, 
                self.current_prompt_id,
                edit_with_ltspice=True
            )
            
            # Connect signals
            edit_worker.ascCodeGenerated.connect(self.on_asc_code_generated)
            edit_worker.imageGenerated.connect(self.middle_panel.set_circuit_image)
            edit_worker.resultReady.connect(self.handle_edit_result)
            
            # Increment prompt ID
            self.current_prompt_id += 1
            
            # Start processing
            edit_worker.start()
                
        except Exception as e:
            error_message = handle_error(e, self, "Failed to edit with LTSpice")
            self.right_panel.receive_message(f"Error: {error_message}")
            
            # Reset processing state
            self.is_processing = False
            self.right_panel.set_processing(False)
            
    def handle_edit_result(self, result):
        """Handle edit result"""
        try:
            if result.get("success", False):
                self.right_panel.receive_message("Circuit updated from LTSpice!")
            else:
                self.right_panel.receive_message(f"Error: {result.get('error', 'Failed to edit with LTSpice')}")
        finally:
            # Reset processing state
            self.is_processing = False
            self.right_panel.set_processing(False)
            
    def closeEvent(self, event):
        """Handle application close"""
        logger.info("Application closing")
        
        # Stop any active worker threads
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(1000)  # Wait up to 1 second
            
        # Accept the close event
        event.accept()