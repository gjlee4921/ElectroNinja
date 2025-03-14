# electroninja/ui/main_window.py

import logging
import os
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QApplication, QPushButton
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSlot
from electroninja.config.settings import Config
from electroninja.core.circuit_processor import CircuitProcessor
from electroninja.utils.async_workers import CircuitProcessingWorker
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
        
        # Initialize circuit processor
        self.circuit_processor = CircuitProcessor(self.config)
        
        # Panel widths
        self.left_panel_collapsed_width = 80
        self.left_panel_expanded_width = 300
        
        # Current file path
        self.current_circuit_file = None
        
        # Current prompt tracking
        self.current_prompt_id = 1
        
        # Initialize UI
        self.init_ui()
        self.connect_signals()
        self.adjust_panel_widths()
        
        # Welcome message
        self.right_panel.receive_message(
            "Welcome to ElectroNinja! I'm your AI electrical engineering assistant. "
            "You can ask me to design circuits like 'Create a low-pass filter' or "
            "'Design a voltage divider with 5V input and 2.5V output'. How can I help you today?"
        )
        
    def init_ui(self):
        """Initialize the UI components"""
        # Set up fonts - use QApplication.instance() instead of self.app()
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
        self.left_panel.setMaximumWidth(300)
        
        # Add panels to layout
        self.panels_layout.addWidget(self.left_panel)
        self.panels_layout.addWidget(self.middle_panel)
        self.panels_layout.addWidget(self.right_panel)
        
        # Debug/Test button (uncomment for testing)
        # debug_button = QPushButton("Test Integration", self)
        # debug_button.clicked.connect(self.test_integration)
        # self.right_panel.layout().addWidget(debug_button)
        
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
    
    def test_integration(self):
        """Test integration between components"""
        logger.info("Testing component connections...")
        # Test left panel
        self.left_panel.set_code("Version 4\nSHEET 1 880 680\nWIRE 224 80 80 80")
        # Test middle panel
        test_image = os.path.join(self.config.OUTPUT_DIR, "test_image.png")
        if os.path.exists(test_image):
            self.middle_panel.set_circuit_image(test_image)
        else:
            logger.warning(f"Test image not found: {test_image}")
        # Test right panel
        self.right_panel.receive_message("Test message to chat panel")
        
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
        
        # Check if this is a circuit request
        if self.circuit_processor.is_circuit_request(message):
            # Process as circuit request
            self.process_circuit_request(message)
        else:
            # Generate simple response
            response = self.generate_chat_response(message)
            self.right_panel.receive_message(response)
    
    def generate_chat_response(self, message):
        """Generate a simple chat response for non-circuit messages"""
        logger.info("Generating response for non-circuit message")
        return "I'm trained to help with electronic circuit design. If you'd like me to design a circuit, please ask something like 'Create a voltage divider circuit' or 'Design a low-pass filter'."
            
    def process_circuit_request(self, request):
        """Process a circuit design request"""
        logger.info(f"Processing circuit request: {request}")
        
        # Initial response
        self.right_panel.receive_message(
            "I'll design this circuit for you. Starting the design process..."
        )
        
        # Create worker thread for processing
        self.worker = CircuitProcessingWorker(
            self.circuit_processor.feedback_manager,
            request,
            prompt_id=self.current_prompt_id
        )
        
        # Connect signals
        self.worker.statusUpdate.connect(self.right_panel.receive_message)
        self.worker.ascCodeGenerated.connect(self.left_panel.set_code)
        self.worker.imageGenerated.connect(self.middle_panel.set_circuit_image)
        self.worker.resultReady.connect(self.handle_circuit_result)
        
        # Increment prompt ID for next request
        self.current_prompt_id += 1
        
        # Start processing
        self.worker.start()
        
    # Update the handle_circuit_result method in main_window.py

    def handle_circuit_result(self, result):
        """Handle circuit processing result"""
        if result.get("success", False):
            # Update UI with successful circuit
            if "asc_code" in result:
                self.left_panel.set_code(result["asc_code"])
            if "image_path" in result:
                self.middle_panel.set_circuit_image(result["image_path"])
            if "asc_path" in result:
                self.current_circuit_file = result.get("asc_path")
            
            # Success message - fix grammar for 0 iterations
            iterations = result.get("iterations", 1)
            success_message = f"Circuit successfully verified after {iterations} iteration{'s' if iterations != 1 else ''}!"
            self.right_panel.receive_message(success_message)
        else:
            # Handle failure
            if "error" in result:
                self.right_panel.receive_message(
                    f"Error processing circuit: {result['error']}"
                )
            else:
                iterations = result.get("iterations", 1)
                self.right_panel.receive_message(
                    f"Could not verify circuit after {iterations} iteration{'s' if iterations != 1 else ''}. "
                    "The best attempt is shown."
                )
                
                # Still update UI with best attempt
                if "asc_code" in result:
                    self.left_panel.set_code(result["asc_code"])
                if "image_path" in result:
                    self.middle_panel.set_circuit_image(result["image_path"])
                if "asc_path" in result:
                    self.current_circuit_file = result.get("asc_path")
                    
            logger.error(f"Circuit processing failed: {result.get('error', 'Unknown error')}")
            
    def compile_circuit(self):
        """Manually compile the current circuit"""
        logger.info("Manual circuit compilation requested")
        
        # Get code from editor
        asc_code = self.left_panel.get_code()
        
        if not asc_code.strip():
            QMessageBox.warning(self, "Error", "Please enter circuit code first!")
            return
            
        # Save to file
        if not self.current_circuit_file:
            self.current_circuit_file = os.path.join(self.config.OUTPUT_DIR, "circuit.asc")
            
        try:
            save_file(asc_code, self.current_circuit_file)
            
            # Process circuit
            self.right_panel.receive_message("Processing circuit...")
            
            result = self.circuit_processor.manual_circuit_processing(
                asc_code,
                status_callback=self.right_panel.receive_message
            )
            
            if result.get("success", False):
                self.middle_panel.set_circuit_image(result["image_path"])
                self.right_panel.receive_message("Circuit compiled successfully!")
            else:
                self.right_panel.receive_message(f"Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            error_message = handle_error(e, self, "Failed to compile circuit")
            self.right_panel.receive_message(f"Error: {error_message}")
            
    def edit_with_ltspice(self):
        """Edit circuit in LTSpice"""
        logger.info("Edit with LTSpice requested")
        
        # Get code from editor
        asc_code = self.left_panel.get_code()
        
        if not asc_code.strip():
            QMessageBox.warning(self, "Error", "Please enter circuit code first!")
            return
            
        # Save to file
        if not self.current_circuit_file:
            self.current_circuit_file = os.path.join(self.config.OUTPUT_DIR, "circuit.asc")
            
        try:
            save_file(asc_code, self.current_circuit_file)
            
            # Process circuit with LTSpice
            self.right_panel.receive_message("Opening circuit in LTSpice...")
            
            result = self.circuit_processor.ltspice.process_circuit(
                self.current_circuit_file,
                new_window=True
            )
            
            if result:
                updated_asc_path, image_path = result
                
                # Update UI
                with open(updated_asc_path, "r", encoding="utf-8", errors="replace") as f:
                    updated_code = f.read()
                    
                self.left_panel.set_code(updated_code)
                self.middle_panel.set_circuit_image(image_path)
                self.right_panel.receive_message("Circuit updated from LTSpice!")
                
        except Exception as e:
            error_message = handle_error(e, self, "Failed to edit with LTSpice")
            self.right_panel.receive_message(f"Error: {error_message}")