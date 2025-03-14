import logging
import time
import threading
from typing import Dict, Any, Tuple, List, Optional
from electroninja.config.settings import Config
from electroninja.llm.providers.base import LLMProvider
from electroninja.llm.vector_store import VectorStore
from electroninja.backend.request_evaluator import RequestEvaluator
from electroninja.backend.chat_response_generator import ChatResponseGenerator
from electroninja.backend.circuit_generator import CircuitGenerator
from electroninja.backend.ltspice_manager import LTSpiceManager
from electroninja.backend.vision_processor import VisionProcessor
from electroninja.backend.iteration_controller import IterationController

logger = logging.getLogger('electroninja')

class WorkflowOrchestrator:
    """
    Orchestrates the entire ElectroNinja workflow from user request to final circuit.
    Coordinates all components and manages the overall process flow.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        config: Config = None
    ):
        """
        Initialize the workflow orchestrator.
        
        Args:
            llm_provider: The LLM provider for all AI interactions
            config (Config, optional): Configuration object
        """
        self.config = config or Config()
        self.llm_provider = llm_provider
        
        # Load vector store
        self.vector_store = VectorStore(self.config)
        self.vector_store.load()
        
        # Initialize components
        self.request_evaluator = RequestEvaluator(llm_provider)
        self.chat_generator = ChatResponseGenerator(llm_provider)
        self.circuit_generator = CircuitGenerator(llm_provider, self.vector_store)
        self.ltspice_manager = LTSpiceManager(self.config)
        self.vision_processor = VisionProcessor(self.config)
        self.iteration_controller = IterationController(
            self.circuit_generator,
            self.ltspice_manager,
            self.vision_processor,
            self.chat_generator,
            self.config
        )
        
        self.logger = logger

    def process_request(self, prompt: str, prompt_id: int = 1) -> Dict[str, Any]:
        """
        Process a user request through the complete workflow.
        
        Args:
            prompt (str): User request
            prompt_id (int): ID for the prompt (for folder structure)
            
        Returns:
            Dict[str, Any]: Complete result with all workflow data
        """
        start_time = time.time()
        self.logger.info(f"Processing request: '{prompt}'")
        
        result = {
            "prompt": prompt,
            "prompt_id": prompt_id,
            "is_circuit_related": False,
            "chat_response": "",
            "initial_asc_code": "",
            "iterations": [],
            "final_status": "",
            "success": False,
            "processing_time": 0
        }
        
        # Step 1: Evaluate if the request is circuit-related
        is_circuit_related = self.request_evaluator.is_circuit_related(prompt)
        result["is_circuit_related"] = is_circuit_related
        
        if not is_circuit_related:
            # Handle non-circuit request
            self.logger.info(f"Request not circuit-related: '{prompt}'")
            result["chat_response"] = self.chat_generator.generate_response(prompt, is_circuit_related)
            result["final_status"] = "Not a circuit request"
            
            # Update processing time and return
            result["processing_time"] = time.time() - start_time
            return result
            
        # For circuit-related requests, we'll process in parallel
        chat_thread = threading.Thread(
            target=self._generate_chat_response_thread,
            args=(prompt, is_circuit_related, result)
        )
        
        asc_thread = threading.Thread(
            target=self._generate_asc_code_thread,
            args=(prompt, result)
        )
        
        # Start threads
        chat_thread.start()
        asc_thread.start()
        
        # Wait for threads to complete
        chat_thread.join()
        asc_thread.join()
        
        # Check if ASC generation was successful
        if result["initial_asc_code"].startswith("Error") or result["initial_asc_code"] == "N":
            self.logger.error(f"ASC generation failed for request: '{prompt}'")
            result["final_status"] = "Failed to generate ASC code"
            
            # Update processing time and return
            result["processing_time"] = time.time() - start_time
            return result
            
        # Run the iteration loop
        iteration_result = self.iteration_controller.run_iteration_loop(
            prompt, 
            result["initial_asc_code"], 
            prompt_id
        )
        
        # Update result with iteration data
        result["iterations"] = iteration_result["iterations"]
        result["final_status"] = iteration_result["final_status"]
        result["success"] = iteration_result["success"]
        
        # Update processing time
        result["processing_time"] = time.time() - start_time
        self.logger.info(f"Request processing completed in {result['processing_time']:.2f} seconds")
        
        return result
    
    def _generate_chat_response_thread(self, prompt: str, is_circuit_related: bool, result: Dict[str, Any]) -> None:
        """
        Thread function for generating chat response.
        
        Args:
            prompt (str): User prompt
            is_circuit_related (bool): Whether the prompt is circuit-related
            result (Dict[str, Any]): Result dictionary to update
        """
        try:
            self.logger.info("Starting chat response generation thread")
            chat_response = self.chat_generator.generate_response(prompt, is_circuit_related)
            result["chat_response"] = chat_response
            self.logger.info("Chat response generation completed")
        except Exception as e:
            self.logger.error(f"Error in chat response thread: {str(e)}")
            result["chat_response"] = "I'll try to create a circuit design for you."
    
    def _generate_asc_code_thread(self, prompt: str, result: Dict[str, Any]) -> None:
        """
        Thread function for generating ASC code.
        
        Args:
            prompt (str): User prompt
            result (Dict[str, Any]): Result dictionary to update
        """
        try:
            self.logger.info("Starting ASC code generation thread")
            asc_code = self.circuit_generator.generate_asc_code(prompt)
            result["initial_asc_code"] = asc_code
            self.logger.info("ASC code generation completed")
        except Exception as e:
            self.logger.error(f"Error in ASC generation thread: {str(e)}")
            result["initial_asc_code"] = f"Error: {str(e)}"