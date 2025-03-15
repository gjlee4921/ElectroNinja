import logging
import os
import threading
import time
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.backend.workflow_orchestrator import WorkflowOrchestrator
from electroninja.backend.ltspice_manager import LTSpiceManager

logger = logging.getLogger('electroninja')

class OutputMonitor(QThread):
    """
    Monitors output directories for new ASC code and images during processing.
    Emits signals when new files are detected.
    """
    
    ascCodeDetected = pyqtSignal(str)
    imageDetected = pyqtSignal(str)
    
    def __init__(self, output_dir, prompt_id):
        super().__init__()
        self.output_dir = output_dir
        self.prompt_id = prompt_id
        self.running = False
        self.known_files = set()
        
    def run(self):
        """Run the monitor thread"""
        self.running = True
        
        # Path to prompt directory
        prompt_dir = os.path.join(self.output_dir, f"prompt{self.prompt_id}")
        
        # Initial scan
        self._scan_directory(prompt_dir)
        
        # Monitor loop
        while self.running:
            # Scan for new files
            new_files = self._scan_directory(prompt_dir)
            
            # Process new files
            for file_path in new_files:
                if file_path.endswith(".asc"):
                    try:
                        with open(file_path, "r") as f:
                            asc_code = f.read()
                        self.ascCodeDetected.emit(asc_code)
                        logger.info(f"ASC code detected from file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error reading ASC file: {str(e)}")
                elif file_path.endswith(".png"):
                    self.imageDetected.emit(file_path)
                    logger.info(f"Image detected: {file_path}")
                    
            # Sleep before next scan
            time.sleep(0.5)
            
    def stop(self):
        """Stop the monitor thread"""
        self.running = False
        
    def _scan_directory(self, prompt_dir):
        """
        Scan directory for new files.
        
        Returns:
            list: List of new file paths
        """
        new_files = []
        
        if not os.path.exists(prompt_dir):
            return new_files
            
        # Look for output directories (output0, output1, etc.)
        for item in os.listdir(prompt_dir):
            if item.startswith("output"):
                output_dir = os.path.join(prompt_dir, item)
                
                if os.path.isdir(output_dir):
                    # Check for ASC and PNG files
                    for file_name in os.listdir(output_dir):
                        if file_name in ("code.asc", "image.png"):
                            file_path = os.path.join(output_dir, file_name)
                            
                            if file_path not in self.known_files:
                                self.known_files.add(file_path)
                                new_files.append(file_path)
                                
        return new_files

class ElectroNinjaWorker(QThread):
    """
    Worker thread for processing requests asynchronously.
    Handles communication with the backend workflow orchestrator.
    
    Signals:
        chatResponseGenerated: Emitted when a chat response is generated
        ascCodeGenerated: Emitted when ASC code is generated
        imageGenerated: Emitted when an image is generated
        resultReady: Emitted when the process is complete
    """
    
    # Signals for UI updates
    chatResponseGenerated = pyqtSignal(str)
    ascCodeGenerated = pyqtSignal(str)
    imageGenerated = pyqtSignal(str)
    resultReady = pyqtSignal(dict)
    
    def __init__(self, request, prompt_id, compile_only=False, edit_with_ltspice=False):
        """
        Initialize the worker thread.
        
        Args:
            request (str): User request
            prompt_id (int): ID for the prompt (for folder structure)
            compile_only (bool): If True, only compile the circuit
            edit_with_ltspice (bool): If True, edit the circuit in LTSpice
        """
        super().__init__()
        self.request = request
        self.prompt_id = prompt_id
        self.compile_only = compile_only
        self.edit_with_ltspice = edit_with_ltspice
        self.config = Config()
        
        # Initialize LLM provider
        self.llm_provider = OpenAIProvider(self.config)
        
        # Initialize workflow orchestrator
        self.orchestrator = WorkflowOrchestrator(self.llm_provider, self.config)
        
        # Initialize LTSpice manager for direct compilation
        self.ltspice_manager = LTSpiceManager(self.config)
        
        # Output monitor
        self.monitor = None
        
    def run(self):
        """Execute the worker thread"""
        try:
            # Start output monitor
            self._start_monitor()
            
            # Process the request
            if self.compile_only:
                self._handle_compilation()
            elif self.edit_with_ltspice:
                self._handle_ltspice_edit()
            else:
                self._process_request()
        except Exception as e:
            error_msg = f"Error in worker thread: {str(e)}"
            logger.error(error_msg)
            
            # Signal completion with error
            self.resultReady.emit({
                "success": False,
                "error": str(e)
            })
        finally:
            # Stop output monitor
            self._stop_monitor()
            
    def _start_monitor(self):
        """Start the output monitor"""
        self.monitor = OutputMonitor(self.config.OUTPUT_DIR, self.prompt_id)
        self.monitor.ascCodeDetected.connect(self.ascCodeGenerated)
        self.monitor.imageDetected.connect(self.imageGenerated)
        self.monitor.start()
        
    def _stop_monitor(self):
        """Stop the output monitor"""
        if self.monitor:
            self.monitor.stop()
            self.monitor.wait()
            
    def _process_request(self):
        """Process a user request through the workflow orchestrator"""
        logger.info(f"Processing request: '{self.request}'")
        
        # Monkey patch the workflow orchestrator to capture chat responses
        original_generate_response = self.orchestrator.chat_generator.generate_response
        original_generate_feedback = self.orchestrator.chat_generator.generate_feedback_response
        original_generate_asc = self.orchestrator.circuit_generator.generate_asc_code
        
        def generate_response_hook(prompt, is_circuit_related):
            """Hook to capture chat responses"""
            response = original_generate_response(prompt, is_circuit_related)
            self.chatResponseGenerated.emit(response)
            return response
            
        def generate_feedback_hook(vision_feedback):
            """Hook to capture feedback responses"""
            response = original_generate_feedback(vision_feedback)
            self.chatResponseGenerated.emit(response)
            return response
            
        def generate_asc_hook(prompt):
            """Hook to capture and process ASC code directly"""
            # Fetch similar examples from vector database
            examples = self.orchestrator.vector_store.search(prompt)
            logger.info(f"Found {len(examples)} similar examples for RAG")
            
            # Generate ASC code using the LLM provider with examples directly
            try:
                asc_code = self.orchestrator.llm_provider.generate_asc_code(prompt, examples)
                
                # If it's not a circuit request, return normal result
                if asc_code == "N":
                    return "N"
                
                # Clean ASC code (extract from "Version 4")
                if "Version 4" in asc_code:
                    idx = asc_code.find("Version 4")
                    clean_asc = asc_code[idx:].strip()
                else:
                    # If Version 4 is missing, add it
                    clean_asc = "Version 4\nSHEET 1 880 680\n" + asc_code.strip()
                
                # Emit the ASC code for UI display
                self.ascCodeGenerated.emit(clean_asc)
                
                # Process the circuit with LTSpice immediately
                self._process_with_ltspice(clean_asc)
                
                # Return the cleaned ASC code for the orchestrator
                return clean_asc
            except Exception as e:
                logger.error(f"Error in generate_asc_hook: {str(e)}")
                return f"Error: {str(e)}"
            
        try:
            # Apply the monkey patches
            self.orchestrator.chat_generator.generate_response = generate_response_hook
            self.orchestrator.chat_generator.generate_feedback_response = generate_feedback_hook
            self.orchestrator.circuit_generator.generate_asc_code = generate_asc_hook
            
            # Process the request
            result = self.orchestrator.process_request(self.request, self.prompt_id)
            
            # Signal completion
            self.resultReady.emit(result)
        finally:
            # Restore the original methods
            self.orchestrator.chat_generator.generate_response = original_generate_response
            self.orchestrator.chat_generator.generate_feedback_response = original_generate_feedback
            self.orchestrator.circuit_generator.generate_asc_code = original_generate_asc
    
    def _process_with_ltspice(self, asc_code):
        """
        Process the ASC code with LTSpice directly
        
        Args:
            asc_code (str): ASC code to process
        """
        try:
            logger.info("Processing ASC code with LTSpice directly")
            
            # Process with LTSpice
            result = self.ltspice_manager.process_circuit(asc_code, self.prompt_id, 0)
            
            if result:
                _, image_path = result
                # Emit image path
                self.imageGenerated.emit(image_path)
                logger.info(f"Circuit image generated: {image_path}")
            else:
                logger.error("Failed to process circuit with LTSpice")
        except Exception as e:
            logger.error(f"Error processing with LTSpice: {str(e)}")
        
    def _handle_compilation(self):
        """Handle direct compilation of ASC code"""
        logger.info("Handling direct compilation")
        
        # Extract ASC code (remove "COMPILE:" prefix)
        asc_code = self.request[8:] if self.request.startswith("COMPILE:") else self.request
        
        # Process with LTSpice
        try:
            result = self.ltspice_manager.process_circuit(asc_code, self.prompt_id, 0)
            
            if result:
                asc_path, image_path = result
                
                # Signal success
                self.resultReady.emit({
                    "success": True,
                    "image_path": image_path,
                    "asc_path": asc_path
                })
            else:
                # Signal failure
                self.resultReady.emit({
                    "success": False,
                    "error": "Failed to process circuit with LTSpice"
                })
        except Exception as e:
            # Signal failure
            self.resultReady.emit({
                "success": False,
                "error": str(e)
            })
            
    def _handle_ltspice_edit(self):
        """Handle editing in LTSpice"""
        logger.info("Handling LTSpice edit")
        
        # Extract ASC code (remove "EDIT:" prefix)
        asc_code = self.request[5:] if self.request.startswith("EDIT:") else self.request
        
        # Create output directory
        output_dir = os.path.join(
            self.config.OUTPUT_DIR, 
            f"edit_{self.prompt_id}"
        )
        os.makedirs(output_dir, exist_ok=True)
        
        # Write ASC code to file
        asc_path = os.path.join(output_dir, "circuit.asc")
        with open(asc_path, "w") as f:
            f.write(asc_code)
            
        # Open in LTSpice
        try:
            # Open in LTSpice (assumed to be implemented in LTSpiceInterface)
            self.ltspice_manager.ltspice_interface.open_in_ltspice(asc_path)
            
            # Wait for changes
            original_mtime = os.path.getmtime(asc_path)
            
            # Wait for a maximum of 60 seconds
            for _ in range(60):
                # Sleep for 1 second
                QThread.sleep(1)
                
                # Check if file was modified
                if os.path.exists(asc_path) and os.path.getmtime(asc_path) > original_mtime:
                    # File was modified, read updated content
                    with open(asc_path, "r") as f:
                        updated_asc = f.read()
                        
                    # Signal the updated ASC code
                    self.ascCodeGenerated.emit(updated_asc)
                    
                    # Process with LTSpice to update the image
                    result = self.ltspice_manager.process_circuit(updated_asc, self.prompt_id, 0)
                    
                    if result:
                        _, image_path = result
                        
                        # Signal the image path
                        self.imageGenerated.emit(image_path)
                        
                        # Signal success
                        self.resultReady.emit({
                            "success": True,
                            "image_path": image_path,
                            "asc_path": asc_path,
                            "asc_code": updated_asc
                        })
                        return
            
            # If we get here, the file wasn't modified within the timeout
            self.resultReady.emit({
                "success": False,
                "error": "Timeout waiting for LTSpice edits"
            })
        except Exception as e:
            # Signal failure
            self.resultReady.emit({
                "success": False,
                "error": str(e)
            })