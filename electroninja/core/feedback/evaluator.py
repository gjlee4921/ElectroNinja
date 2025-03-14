# electroninja/core/feedback/evaluator.py
import logging
import re

logger = logging.getLogger('electroninja')

class FeedbackEvaluator:
    """Evaluates circuit feedback to determine success or next steps"""
    
    def __init__(self):
        logger.info("FeedbackEvaluator initialized")
    
    def is_circuit_verified(self, vision_feedback):
        """
        Check if the vision feedback indicates the circuit is verified
        
        Args:
            vision_feedback (str): Vision feedback from vision model
            
        Returns:
            bool: True if verified, False otherwise
        """
        # With OpenAI, verification is simply if the feedback is exactly 'Y'
        is_verified = vision_feedback.strip() == 'Y'
        
        verification_message = "Circuit passed verification" if is_verified else "Circuit failed verification"
        logger.info(f"{verification_message}")
            
        return is_verified
        
    def extract_feedback_points(self, vision_feedback):
        """
        Extract key feedback points from vision feedback
        
        Args:
            vision_feedback (str): Vision feedback
            
        Returns:
            list: List of feedback points
        """
        # If verified (just 'Y'), there are no feedback points
        if self.is_circuit_verified(vision_feedback):
            return ["Circuit correctly implements the request"]
        
        # For more detailed analysis, try to extract structured points
        # Look for numbered points (1., 2., etc.) or paragraph boundaries
        numbered_pattern = r'\b\d+\.[\s]+(.*?)(?=\b\d+\.[\s]+|$)'
        numbered_matches = re.findall(numbered_pattern, vision_feedback)
        
        if numbered_matches:
            # If we found numbered points, return those
            return [point.strip() for point in numbered_matches if point.strip()]
        
        # Otherwise split by paragraphs
        paragraphs = vision_feedback.split('\n\n')
        if len(paragraphs) > 1:
            return [p.strip() for p in paragraphs if p.strip()]
        
        # As a fallback, split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', vision_feedback.strip())
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 15]  # Only reasonably long sentences
        
        if meaningful_sentences:
            return meaningful_sentences
        
        # Final fallback
        return ["Circuit does not correctly implement the request"]
        
    def format_iteration_result(self, state, current_asc, image_path, feedback, success=False):
        """
        Format the result of an iteration
        
        Args:
            state (dict): Current state
            current_asc (str): Current ASC code
            image_path (str): Path to the circuit image
            feedback (str): Vision feedback
            success (bool): Whether the circuit is verified
            
        Returns:
            dict: Formatted result
        """
        # Extract feedback points
        feedback_points = self.extract_feedback_points(feedback)
        
        return {
            "success": success,
            "iterations": state["iteration"],
            "asc_code": current_asc,
            "image_path": image_path,
            "feedback": feedback,
            "feedback_points": feedback_points,
            "history": state["history"]
        }