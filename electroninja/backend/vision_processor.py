import logging
from typing import Optional
from electroninja.config.settings import Config
from electroninja.llm.vision_analyser import VisionAnalyzer
from electroninja.utils.error_handler import ModelError

logger = logging.getLogger('electroninja')

class VisionProcessor:
    """
    Processes circuit images with the vision model to evaluate correctness.
    Analyzes whether a circuit meets the requirements or needs improvements.
    """

    def __init__(self, config: Config = None):
        """
        Initialize the vision processor.
        
        Args:
            config (Config, optional): Configuration object. If None, a new one is created.
        """
        self.config = config or Config()
        self.vision_analyzer = VisionAnalyzer(self.config)
        self.logger = logger

    def analyze_circuit_image(self, image_path: str, original_request: str) -> str:
        """
        Analyze a circuit image to determine if it correctly implements the request.
        
        Args:
            image_path (str): Path to the circuit image
            original_request (str): Original user request
            
        Returns:
            str: Vision analysis result. 'Y' if the circuit is correct, 
                 or detailed feedback about issues if incorrect.
        """
        try:
            self.logger.info(f"Analyzing circuit image for request: '{original_request}'")
            
            # Analyze the image using the vision analyzer
            analysis = self.vision_analyzer.analyze_circuit_image(image_path, original_request)
            
            # Check if the circuit is correct (vision model returns 'Y')
            is_correct = analysis.strip() == 'Y'
            self.logger.info(f"Circuit analysis complete. Correct: {is_correct}")
            
            return analysis
            
        except Exception as e:
            error_msg = f"Error analyzing circuit image: {str(e)}"
            self.logger.error(error_msg)
            return f"Error: {error_msg}"

    def is_circuit_verified(self, vision_feedback: str) -> bool:
        """
        Check if the circuit has been verified by the vision model.
        
        Args:
            vision_feedback (str): Feedback from the vision model
            
        Returns:
            bool: True if the circuit is verified (vision feedback is 'Y'), False otherwise
        """
        return vision_feedback.strip() == 'Y'