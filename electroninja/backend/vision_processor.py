import logging
import os
from electroninja.config.settings import Config
from electroninja.llm.vision_analyser import VisionAnalyzer

logger = logging.getLogger('electroninja')

class VisionProcessor:
    """
    Processes circuit images with the vision model to evaluate correctness.
    """
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.vision_analyzer = VisionAnalyzer(self.config)
        self.logger = logger

    def analyze_circuit_image(self, image_path: str, original_request: str) -> str:
        self.logger.info(f"Analyzing circuit image for request: '{original_request}'")
        
        # Print input information
        print(f"\n{'='*80}\nVISION PROCESSOR INPUT:\n{'='*80}")
        print(f"Image path: {image_path}")
        print(f"Original request: {original_request}")
        # Print if the image exists
        if os.path.exists(image_path):
            file_size = os.path.getsize(image_path)
            print(f"Image exists: Yes (Size: {file_size} bytes)")
        else:
            print(f"Image exists: No")
        print('='*80)
        
        # Analyze the image
        analysis = self.vision_analyzer.analyze_circuit_image(image_path, original_request)
        
        # Print the analysis result
        is_correct = analysis.strip() == 'Y'
        print(f"\n{'='*80}\nVISION PROCESSOR OUTPUT:\n{'='*80}")
        print(f"Analysis result: {analysis}")
        print(f"Circuit verified as correct: {is_correct}")
        print('='*80)
        
        self.logger.info(f"Circuit analysis complete. Correct: {is_correct}")
        return analysis

    def is_circuit_verified(self, vision_feedback: str) -> bool:
        return vision_feedback.strip() == 'Y'