import logging
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
        analysis = self.vision_analyzer.analyze_circuit_image(image_path, original_request)
        is_correct = analysis.strip() == 'Y'
        self.logger.info(f"Circuit analysis complete. Correct: {is_correct}")
        return analysis

    def is_circuit_verified(self, vision_feedback: str) -> bool:
        return vision_feedback.strip() == 'Y'
