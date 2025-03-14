import os
import logging
from electroninja.config.settings import Config
from electroninja.core.feedback.loop_manager import FeedbackLoopManager
from electroninja.core.ltspice.interface import LTSpiceInterface
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.llm.vector_store import VectorStore
from electroninja.utils.file_operations import save_file
from electroninja.utils.error_handler import LTSpiceError

logger = logging.getLogger('electroninja')

class CircuitProcessor:
    """Main entry point for circuit processing"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.feedback_manager = FeedbackLoopManager(self.config)
        self.ltspice = LTSpiceInterface(self.config)
        self.llm_provider = OpenAIProvider(self.config)
        self.vector_store = VectorStore(self.config)
        
        # Load vector store
        self.vector_store.load()
        
    def process_circuit_request(self, request, status_callback=None):
        """
        Process a circuit request
        
        Args:
            request (str): User request
            status_callback (function): Callback for status updates
            
        Returns:
            dict: Result of processing
        """
        try:
            # Search for similar examples
            examples = self.vector_store.search(request)
            
            # Process the request
            result = self.feedback_manager.process_request(
                request,
                examples=examples,
                status_callback=status_callback
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Circuit processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def is_circuit_request(self, message):
        """
        Check if a message is a circuit request
        
        Args:
            message (str): User message
            
        Returns:
            bool: True if it's a circuit request
        """
        keywords = ["circuit", "resistor", "capacitor", "oscillator", "filter", 
                    "transistor", "diode", "voltage", "current", "amplifier"]
        return any(kw in message.lower() for kw in keywords)
        
    def manual_circuit_processing(self, asc_code, status_callback=None, prompt_id=None, iteration=0):
        """
        Process a circuit manually
        
        Args:
            asc_code (str): ASC code
            status_callback (function): Callback for status updates
            prompt_id (int, optional): Prompt ID for organizing outputs
            iteration (int, optional): Iteration number
            
        Returns:
            dict: Result of processing
        """
        try:
            # If prompt_id not provided, use a default
            if prompt_id is None:
                prompt_id = 1
            
            if status_callback:
                status_callback(f"Processing circuit in LTSpice...")
                
            # Process using the LTSpice interface directly
            result = self.ltspice.process_circuit(
                asc_code,
                prompt_id=prompt_id,
                iteration=iteration
            )
            
            if not result:
                raise LTSpiceError("LTSpice processing failed")
                
            updated_asc_path, image_path = result
            
            # Read the updated ASC code
            with open(updated_asc_path, 'r', encoding='utf-8', errors='replace') as f:
                updated_asc_code = f.read()
            
            return {
                "success": True,
                "asc_path": updated_asc_path,
                "image_path": image_path,
                "asc_code": updated_asc_code
            }
            
        except Exception as e:
            logger.error(f"Manual circuit processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_existing_circuit(self, asc_code, prompt_id=None, iteration=0, status_callback=None):
        """
        Process an existing circuit that was loaded or edited
        
        Args:
            asc_code (str): ASC code
            prompt_id (int, optional): Prompt ID for organizing outputs
            iteration (int, optional): Iteration number
            status_callback (function, optional): Callback for status updates
            
        Returns:
            dict: Result of processing
        """
        try:
            # Default prompt_id if not provided
            if prompt_id is None:
                prompt_id = 1
            
            # Status update
            if status_callback:
                status_callback("Processing existing circuit in LTSpice...")
            
            # Process with LTSpice
            result = self.ltspice.process_circuit(
                asc_code,
                prompt_id=prompt_id,
                iteration=iteration
            )
            
            if not result:
                raise LTSpiceError("LTSpice processing failed")
                
            updated_asc_path, image_path = result
            
            # Read updated ASC code
            with open(updated_asc_path, 'r', encoding='utf-8', errors='replace') as f:
                updated_asc_code = f.read()
            
            return {
                "success": True,
                "asc_path": updated_asc_path,
                "image_path": image_path,
                "asc_code": updated_asc_code
            }
            
        except Exception as e:
            logger.error(f"Existing circuit processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
