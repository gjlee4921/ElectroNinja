# electroninja/llm/vision_analyser.py
import os
import logging
import base64
import openai
from electroninja.config.settings import Config
from electroninja.llm.prompts.circuit_prompts import VISION_IMAGE_ANALYSIS_PROMPT

logger = logging.getLogger('electroninja')

class VisionAnalyzer:
    """Analyzes circuit images using OpenAI's vision model"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.model = self.config.OPENAI_VISION_MODEL  # Should be "gpt-4o"
        openai.api_key = self.config.OPENAI_API_KEY
        logger.info(f"Vision Analyzer initialized with OpenAI model: {self.model}")
        
    def analyze_circuit_image(self, image_path, original_request):
        """
        Analyze a circuit image to determine if it satisfies the user's request
        
        Args:
            image_path (str): Path to the circuit image
            original_request (str): Original user request
            
        Returns:
            str: Analysis result with 'Y' if verified, or detailed feedback
        """
        try:
            logger.info(f"Starting analysis of circuit image: {image_path}")
            logger.info(f"Original request: '{original_request}'")
            
            if not os.path.exists(image_path):
                error_msg = f"Image file not found: {image_path}"
                logger.error(error_msg)
            
            # Get file size for logging
            file_size = os.path.getsize(image_path)
            logger.info(f"Image file size: {file_size} bytes")
                
            # Encode image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                logger.info(f"Successfully encoded image data (length: {len(image_data)})")
                
            # Use the OpenAI prompt template
            prompt = VISION_IMAGE_ANALYSIS_PROMPT.format(original_request=original_request)
            
            logger.info(f"Sending request to OpenAI vision model ({self.model})...")
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Extract and process analysis
            analysis = response.choices[0].message.content.strip()
            
            # No logging of raw output to avoid encoding issues
            # Just log the status
            is_verified = analysis.strip() == 'Y'
            verification_status = "VERIFIED" if is_verified else "NOT VERIFIED"
            logger.info(f"Vision analysis complete: Circuit {verification_status}")
            
            # Return the raw analysis
            return analysis
            
        except Exception as e:
            error_msg = f"Vision analysis error: {str(e)}"
            logger.error(error_msg)