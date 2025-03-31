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
        
    def analyze_circuit_image(self, image_path, circuit_description):
        """
        Analyze a circuit image to determine if it satisfies the circuit description.
        
        Args:
            image_path (str): Path to the circuit image.
            circuit_description (str): The circuit description loaded from file.
            
        Returns:
            str: 'Y' if the circuit is verified, or detailed feedback if not.
        """
        try:
            logger.info(f"Starting analysis of circuit image: {image_path}")
            logger.info(f"Circuit description for analysis: '{circuit_description[:50]}...'")
            
            if not os.path.exists(image_path):
                error_msg = f"Image file not found: {image_path}"
                logger.error(error_msg)
                return f"Error: {error_msg}"
            
            # Log file size
            file_size = os.path.getsize(image_path)
            logger.info(f"Image file size: {file_size} bytes")
                
            # Encode image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                logger.info(f"Successfully encoded image data (length: {len(image_data)})")
                
            # Build the prompt using the circuit description
            prompt = VISION_IMAGE_ANALYSIS_PROMPT.format(description=circuit_description)
            logger.info("Sending prompt to OpenAI vision model...")
            
            # Call OpenAI API with both text and the image data
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
                                    "url": f"data:image/png;base64,{image_data}",
                                    "detail": "high",
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Extract and process analysis
            analysis = response.choices[0].message.content.strip()
            is_verified = analysis == 'Y'
            verification_status = "VERIFIED" if is_verified else "NOT VERIFIED"
            logger.info(f"Vision analysis complete: Circuit {verification_status}")
            
            return analysis
            
        except Exception as e:
            error_msg = f"Vision analysis error: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
