# electroninja/ui/main_window.py

import logging
import os
import re
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSlot
from electroninja.config.settings import Config
from electroninja.utils.async_workers import ElectroNinjaWorker
from electroninja.utils.error_handler import handle_error
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
        
        # Current tracking
        self.current_prompt_id = 1
        self.current_iteration = 0
        
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
        logger.info(f"Processing user message: {message[:50]}...")
        
        # Ignore if already processing
        if self.is_processing:
            return
            
        # Set processing state
        self.is_processing = True
        self.right_panel.set_processing(True)
        
        # Add the user message to chat
        self.right_panel.chat_panel.add_message(message, is_user=True)
        
        # Ensure left panel is expanded to show the code
        if not self.left_panel.is_expanded:
            self.on_left_panel_toggle(True)
        
        # Clear previous content
        self.left_panel.clear_code()
        self.middle_panel.clear_image()
        self.current_iteration = 0
        
        # Process the request
        self.process_request(message)
    
    def process_request(self, request):
        """Process a user request"""
        logger.info(f"Creating worker for request: {request[:50]}...")
        
        # Create worker thread for processing
        self.worker = ElectroNinjaWorker(request, self.current_prompt_id)
        
        # Connect signals - ensure all needed signals are connected
        self.worker.chatResponseGenerated.connect(self.on_chat_response)
        self.worker.ascCodeGenerated.connect(self.on_asc_code_generated)
        self.worker.imageGenerated.connect(self.on_image_generated)
        self.worker.visionFeedbackGenerated.connect(self.on_vision_feedback)
        self.worker.resultReady.connect(self.handle_result)
        
        # Increment prompt ID for next request
        self.current_prompt_id += 1
        
        # Start processing
        self.worker.start()
        
    def on_chat_response(self, message):
        """Process chat response, checking for tags"""
        message_type = "normal"
        clean_message = message
        
        # Extract tags if present
        if "[INITIAL]" in message:
            message_type = "initial"
            clean_message = message.replace("[INITIAL]", "").strip()
        elif "[REFINING]" in message:
            message_type = "refining"
            clean_message = message.replace("[REFINING]", "").strip()
        elif "[COMPLETE]" in message:
            message_type = "complete"
            clean_message = message.replace("[COMPLETE]", "").strip()
        
        # Send to right panel with type information
        self.right_panel.receive_message_with_type(clean_message, message_type)
        
    def on_asc_code_generated(self, asc_code):
        """Handle ASC code generation with animation and iteration tracking"""
        # Skip empty or non-circuit responses
        if not asc_code or asc_code == "N":
            return
            
        # Process iteration tags if present
        iteration_tag = ""
        clean_asc_code = asc_code
        
        if "[INITIAL]" in asc_code:
            clean_asc_code = asc_code.replace("[INITIAL]", "").strip()
            self.current_iteration = 0
            iteration_tag = "Initial Circuit"
        elif "[ITERATION" in asc_code:
            match = re.search(r'\[ITERATION (\d+)\]', asc_code)
            if match:
                self.current_iteration = int(match.group(1))
                iteration_tag = f"Iteration {self.current_iteration}"
                clean_asc_code = re.sub(r'\[ITERATION \d+\]', '', asc_code).strip()
        
        # Add version marker if missing
        if not clean_asc_code.startswith("Version 4"):
            clean_asc_code = "Version 4\nSHEET 1 880 680\n" + clean_asc_code
        
        # Update iteration display
        if iteration_tag:
            self.left_panel.update_iteration_label(iteration_tag)
            
        # Set the code with animation
        self.left_panel.set_code(clean_asc_code, animated=True)
        
    def on_image_generated(self, image_path):
        """Process image generation, extracting iteration info"""
        # Extract iteration number if present
        if "output" in image_path:
            try:
                match = re.search(r'output(\d+)', image_path)
                if match:
                    iteration = int(match.group(1))
                    self.current_iteration = iteration
            except:
                pass
                
        # Update middle panel
        self.middle_panel.set_circuit_image(image_path, self.current_iteration)

    def on_vision_feedback(self, feedback):
        """Handle vision feedback"""
        logger.info(f"Received vision feedback: {'Y' if feedback.strip() == 'Y' else 'Needs improvement'}")
        
        # The chat response will be handled by the feedback_response_hook
        # This is just for logging or any additional UI updates

    def handle_result(self, result):
        """Handle processing result"""
        try:
            # Just reset processing state, let LLM handle any messages
            pass
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