import logging
import os
from typing import Tuple, Optional
from electroninja.config.settings import Config
from electroninja.core.ltspice.interface import LTSpiceInterface
from electroninja.utils.error_handler import LTSpiceError

logger = logging.getLogger('electroninja')

class LTSpiceManager:
    """
    Manages the processing of ASC code with LTSpice.
    Handles file management, LTSpice execution, and image generation.
    """

    def __init__(self, config: Config = None):
        """
        Initialize the LTSpice manager.
        
        Args:
            config (Config, optional): Configuration object. If None, a new one is created.
        """
        self.config = config or Config()
        self.ltspice_interface = LTSpiceInterface(self.config)
        self.logger = logger

    def process_circuit(self, asc_code: str, prompt_id: int, iteration: int) -> Optional[Tuple[str, str]]:
        """
        Process a circuit by:
        1. Creating output folders.
        2. Writing the ASC file.
        3. Using LTSpice to generate a visual representation.
        4. Converting to a PNG image.
        
        Args:
            asc_code (str): The ASC code to process
            prompt_id (int): The ID of the user prompt (for folder structure)
            iteration (int): The iteration number (for folder structure)
            
        Returns:
            Optional[Tuple[str, str]]: (asc_path, image_path) or None if processing failed
        """
        try:
            self.logger.info(f"Processing circuit with LTSpice (Prompt {prompt_id}, Iteration {iteration})")
            
            # Process the circuit using the LTSpice interface
            result = self.ltspice_interface.process_circuit(asc_code, prompt_id=prompt_id, iteration=iteration)
            
            if not result:
                self.logger.error("LTSpice processing failed")
                return None
                
            asc_path, image_path = result
            
            # Verify that the files exist
            if not os.path.exists(asc_path) or not os.path.exists(image_path):
                self.logger.error(f"Expected output files not found: ASC={os.path.exists(asc_path)}, Image={os.path.exists(image_path)}")
                return None
                
            self.logger.info(f"LTSpice processing successful. ASC: {asc_path}, Image: {image_path}")
            return asc_path, image_path
            
        except LTSpiceError as e:
            self.logger.error(f"LTSpice error: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in LTSpice processing: {str(e)}")
            return None

    def get_output_paths(self, prompt_id: int, iteration: int) -> Tuple[str, str]:
        """
        Get the output paths for a given prompt and iteration.
        
        Args:
            prompt_id (int): The ID of the user prompt
            iteration (int): The iteration number
            
        Returns:
            Tuple[str, str]: (asc_path, image_path)
        """
        output_dir = os.path.join(
            self.config.OUTPUT_DIR, 
            f"prompt{prompt_id}", 
            f"output{iteration}"
        )
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        asc_path = os.path.join(output_dir, "code.asc")
        image_path = os.path.join(output_dir, "image.png")
        
        return asc_path, image_path