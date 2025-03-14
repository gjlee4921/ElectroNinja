# electroninja/core/feedback/loop_manager.py

import os
import logging
from electroninja.config.settings import Config
from electroninja.core.ltspice.interface import LTSpiceInterface
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.llm.vector_store import VectorStore
from electroninja.llm.vision_analyser import VisionAnalyzer
from electroninja.core.feedback.state_tracker import StateTracker
from electroninja.core.feedback.evaluator import FeedbackEvaluator
from electroninja.utils.file_operations import save_file
from electroninja.utils.error_handler import LTSpiceError, ModelError

logger = logging.getLogger('electroninja')

class FeedbackLoopManager:
    """Manages the iterative feedback loop for circuit design and refinement"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        
        # Initialize components
        self.llm_provider = OpenAIProvider(self.config)
        self.ltspice = LTSpiceInterface(self.config)
        self.vector_store = VectorStore(self.config)
        self.vision_analyzer = VisionAnalyzer(self.config)
        self.evaluator = FeedbackEvaluator()
        
        # Load vector store
        try:
            self.vector_store.load()
            logger.info("Vector store loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load vector store: {str(e)}")
    
    def process_request(self, request, prompt_id=1, examples=None, max_iterations=3, status_callback=None):
        """
        Process a circuit request through the iterative feedback loop
        
        Args:
            request (str): User request for circuit design
            prompt_id (int): Identifier for this request (for file organization)
            examples (list): Optional list of example circuits
            max_iterations (int): Maximum number of iterations to attempt
            status_callback (function): Optional callback for status updates
            
        Returns:
            dict: Result dictionary with status, code, images, and history
        """
        # Initialize state tracker
        state_tracker = StateTracker(request, max_iterations=max_iterations)
        
        # Step 1: Evaluate if the request is circuit-related
        if status_callback:
            status_callback("Evaluating if your request is related to electrical circuits...")
        
        try:
            is_circuit_related = self.llm_provider.evaluate_circuit_request(request)
            
            if not is_circuit_related:
                if status_callback:
                    status_callback("I'm sorry, but your request doesn't appear to be related to electrical circuits. "
                                  "I'm specifically designed to help with circuit design tasks.")
                return {
                    "success": False,
                    "error": "Request not related to circuits",
                    "is_circuit_related": False
                }
                
            # Generate initial ASC code
            if status_callback:
                status_callback("Generating circuit design based on your request...")
            
            if examples is None:
                # Fetch examples from vector database
                examples = self.vector_store.search(request)
                
            # Generate ASC code
            asc_code = self.llm_provider.generate_asc_code(request, examples)
            
            if not asc_code or asc_code == "N" or asc_code.startswith("Error"):
                if status_callback:
                    status_callback("I'm sorry, but I couldn't generate a valid circuit for your request. "
                                  "Could you please provide more details or try a different circuit?")
                return {
                    "success": False,
                    "error": "Failed to generate ASC code",
                    "is_circuit_related": True
                }
            
            # Store the initial ASC code
            state_tracker.add_asc_attempt(state_tracker.get_iteration(), asc_code)
            current_asc_code = asc_code
            
            # Prepare for iterations
            best_result = None
            image_path = None
            asc_path = None
            
            # Iterate until success or max iterations reached
            while not state_tracker.is_max_iterations_reached():
                iteration = state_tracker.get_iteration()
                
                # Process with LTSpice
                if status_callback:
                    status_callback(f"Processing circuit with LTSpice (Iteration {iteration + 1}/{max_iterations})...")
                
                try:
                    # Save the ASC code to a file
                    temp_asc_path = os.path.join(self.config.OUTPUT_DIR, f"prompt{prompt_id}", f"output{iteration}", "code.asc")
                    os.makedirs(os.path.dirname(temp_asc_path), exist_ok=True)
                    save_file(current_asc_code, temp_asc_path)
                    
                    # Process with LTSpice
                    ltspice_result = self.ltspice.process_circuit(
                        current_asc_code,
                        prompt_id=prompt_id,
                        iteration=iteration
                    )
                    
                    if not ltspice_result:
                        if status_callback:
                            status_callback("There was an issue processing the circuit with LTSpice. "
                                          "I'll try to fix it in the next iteration.")
                        
                        if best_result is None:
                            best_result = {
                                "success": False,
                                "error": "LTSpice processing failed",
                                "asc_code": current_asc_code,
                                "iterations": iteration + 1,
                                "history": state_tracker.get_history()
                            }
                        
                        # Try next iteration with refinement if possible
                        if iteration < max_iterations - 1:
                            state_tracker.increment_iteration()
                            current_asc_code = self.llm_provider.refine_asc_code(request, state_tracker.get_history())
                            continue
                        else:
                            break
                    
                    asc_path, image_path = ltspice_result
                    
                    # Analyze with vision model
                    if status_callback:
                        status_callback("Analyzing the circuit image to verify correctness...")
                    
                    vision_feedback = self.vision_analyzer.analyze_circuit_image(image_path, request)
                    state_tracker.add_vision_feedback(iteration, vision_feedback)
                    
                    # Generate user-friendly feedback
                    feedback_response = self.llm_provider.generate_vision_feedback_response(vision_feedback)
                    if status_callback:
                        status_callback(feedback_response)
                    
                    # Check if circuit is verified
                    is_verified = self.evaluator.is_circuit_verified(vision_feedback)
                    
                    # Store the current best result
                    current_result = self.evaluator.format_iteration_result(
                        state_tracker.get_state(),
                        current_asc_code,
                        image_path,
                        vision_feedback,
                        success=is_verified
                    )
                    
                    # Always update the best result to have the latest information
                    best_result = current_result
                    
                    if is_verified:
                        # Circuit is correct, we're done!
                        state_tracker.set_success(True)
                        if status_callback:
                            status_callback("Success! The circuit has been verified and meets all requirements.")
                        break
                    
                    # Check if we should continue
                    if iteration >= max_iterations - 1:
                        if status_callback:
                            status_callback("I've reached the maximum number of refinement iterations. "
                                          "The current circuit is the best I could design based on your request.")
                        break
                    
                    # Refine ASC code for next iteration
                    if status_callback:
                        status_callback("Refining the circuit based on analysis feedback...")
                    
                    # Increment iteration for next cycle
                    state_tracker.increment_iteration()
                    
                    # Refine the ASC code
                    refined_asc_code = self.llm_provider.refine_asc_code(request, state_tracker.get_history())
                    
                    if not refined_asc_code or refined_asc_code.startswith("Error"):
                        if status_callback:
                            status_callback("I'm having trouble refining the circuit. "
                                          "I'll use the best design created so far.")
                        break
                    
                    # Update for next iteration
                    current_asc_code = refined_asc_code
                    state_tracker.add_asc_attempt(state_tracker.get_iteration(), current_asc_code)
                    
                except Exception as e:
                    logger.error(f"Error in iteration {iteration}: {str(e)}")
                    if status_callback:
                        status_callback(f"An error occurred during processing: {str(e)}")
                    
                    if best_result is None:
                        best_result = {
                            "success": False,
                            "error": str(e),
                            "asc_code": current_asc_code,
                            "iterations": iteration + 1,
                            "history": state_tracker.get_history()
                        }
                    break
            
            # If we somehow got here without setting best_result
            if best_result is None:
                best_result = {
                    "success": False,
                    "error": "Unknown error during processing",
                    "asc_code": current_asc_code,
                    "iterations": state_tracker.get_iteration() + 1,
                    "history": state_tracker.get_history()
                }
            
            # Add the final paths to the result
            if asc_path:
                best_result["asc_path"] = asc_path
            if image_path:
                best_result["image_path"] = image_path
            
            return best_result
            
        except Exception as e:
            logger.error(f"Error in feedback loop: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            if status_callback:
                status_callback(f"An error occurred: {str(e)}")
                
            return {
                "success": False,
                "error": str(e),
                "iterations": 0
            }