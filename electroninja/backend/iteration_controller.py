import logging
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from electroninja.config.settings import Config
from electroninja.backend.circuit_generator import CircuitGenerator
from electroninja.backend.ltspice_manager import LTSpiceManager
from electroninja.backend.vision_processor import VisionProcessor
from electroninja.backend.chat_response_generator import ChatResponseGenerator

logger = logging.getLogger('electroninja')

class IterationController:
    """
    Controls the iterative refinement process for circuit design.
    Manages the feedback loop between ASC generation, LTSpice processing,
    vision analysis, and refinement until the circuit is verified or
    maximum iterations are reached.
    """

    def __init__(
        self, 
        circuit_generator: CircuitGenerator,
        ltspice_manager: LTSpiceManager,
        vision_processor: VisionProcessor,
        chat_generator: ChatResponseGenerator,
        config: Config = None
    ):
        """
        Initialize the iteration controller.
        
        Args:
            circuit_generator: For generating and refining ASC code
            ltspice_manager: For processing circuits with LTSpice
            vision_processor: For analyzing circuit images
            chat_generator: For generating feedback responses
            config (Config, optional): Configuration object
        """
        self.circuit_generator = circuit_generator
        self.ltspice_manager = ltspice_manager
        self.vision_processor = vision_processor
        self.chat_generator = chat_generator
        self.config = config or Config()
        self.max_iterations = self.config.MAX_ITERATIONS
        self.logger = logger
        
    def run_iteration_loop(self, prompt: str, initial_asc_code: str, prompt_id: int) -> Dict[str, Any]:
        """
        Run the iteration loop for circuit refinement.
        
        Args:
            prompt (str): Original user request
            initial_asc_code (str): Initial ASC code
            prompt_id (int): ID for the prompt (for folder structure)
            
        Returns:
            Dict[str, Any]: Result with all iteration data
        """
        self.logger.info(f"Starting iteration loop for prompt: '{prompt}'")
        
        result = {
            "prompt": prompt,
            "prompt_id": prompt_id,
            "iterations": [],
            "final_status": "",
            "success": False
        }
        
        # Initialize loop state
        current_iteration = 0
        history = []
        circuit_verified = False
        current_asc_code = initial_asc_code
        
        # Run iterations until the circuit is verified or we reach the maximum
        while current_iteration < self.max_iterations:
            self.logger.info(f"Starting iteration {current_iteration}")
            
            # Step 1: Process with LTSpice
            ltspice_result = self.ltspice_manager.process_circuit(
                current_asc_code, 
                prompt_id=prompt_id, 
                iteration=current_iteration
            )
            
            if not ltspice_result:
                self.logger.error(f"LTSpice processing failed (iteration {current_iteration})")
                result["final_status"] = f"Failed at iteration {current_iteration}: LTSpice processing error"
                break
                
            asc_path, image_path = ltspice_result
            
            # Step 2: Analyze with vision model
            vision_feedback = self.vision_processor.analyze_circuit_image(image_path, prompt)
            
            # Step 3: Generate user-friendly feedback
            feedback_response = self.chat_generator.generate_feedback_response(vision_feedback)
            
            # Record iteration data
            iteration_data = {
                "iteration": current_iteration,
                "asc_code": current_asc_code,
                "asc_path": asc_path,
                "image_path": image_path,
                "vision_feedback": vision_feedback,
                "feedback_response": feedback_response
            }
            
            # Add to history and result
            history.append(iteration_data)
            result["iterations"].append(iteration_data)
            
            # Check if circuit is verified
            circuit_verified = self.vision_processor.is_circuit_verified(vision_feedback)
            if circuit_verified:
                self.logger.info(f"Circuit verified at iteration {current_iteration}")
                result["final_status"] = f"Circuit verified at iteration {current_iteration}"
                result["success"] = True
                break
                
            # Check if we should continue
            if current_iteration >= self.max_iterations - 1:
                self.logger.info(f"Reached maximum iterations ({self.max_iterations})")
                result["final_status"] = f"Maximum iterations reached ({self.max_iterations})"
                break
                
            # Refine ASC code for next iteration
            self.logger.info(f"Refining ASC code for iteration {current_iteration + 1}")
            refined_asc_code = self.circuit_generator.refine_asc_code(prompt, history)
            
            # Check for basic format only - no validation
            if not refined_asc_code or refined_asc_code == "N":
                self.logger.warning(f"ASC refinement returned empty or N (iteration {current_iteration})")
                # We'll still try to use it
            
            # Log any error message but continue anyway
            if refined_asc_code.startswith("Error:"):
                self.logger.warning(f"ASC refinement returned error (iteration {current_iteration}): {refined_asc_code}")
                # Continue anyway, the error message might get rendered in LTSpice
            
            # Update for next iteration - always use what we got
            iteration_data["refined_asc_code"] = refined_asc_code
            current_asc_code = refined_asc_code
            current_iteration += 1
            
        # Save complete history to JSON file
        self._save_iteration_history(prompt, result)
        
        return result
    
    def _save_iteration_history(self, prompt: str, result: Dict[str, Any]) -> None:
        """
        Save the complete iteration history to a JSON file.
        
        Args:
            prompt (str): Original user prompt
            result (Dict[str, Any]): Iteration result data
        """
        try:
            prompt_id = result.get("prompt_id", 1)
            history_path = os.path.join(
                self.config.OUTPUT_DIR,
                f"pipeline_history_prompt{prompt_id}.json"
            )
            
            with open(history_path, "w") as f:
                json.dump(result, f, indent=2)
                
            self.logger.info(f"Saved iteration history to {history_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving iteration history: {str(e)}")