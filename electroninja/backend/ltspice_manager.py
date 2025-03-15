import logging
import os
from typing import Tuple, Optional
from electroninja.config.settings import Config
from electroninja.core.ltspice.interface import LTSpiceInterface

logger = logging.getLogger('electroninja')

class LTSpiceManager:
    """
    Manages the processing of ASC code with LTSpice.
    """
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.ltspice_interface = LTSpiceInterface(self.config)
        self.logger = logger

    def process_circuit(self, asc_code: str, prompt_id: int, iteration: int) -> Optional[Tuple[str, str]]:
        try:
            asc_path, image_path = self.get_output_paths(prompt_id, iteration)
            output_dir = os.path.dirname(asc_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                self.logger.info(f"Created output structure: {output_dir}")
            with open(asc_path, 'w') as f:
                f.write(asc_code)
            self.logger.info(f"Wrote ASC file: {asc_path}")
            self.logger.info(f"Processing circuit with LTSpice (Prompt {prompt_id}, Iteration {iteration})")
            result = self.ltspice_interface.process_circuit(asc_code, prompt_id=prompt_id, iteration=iteration)
            if not result:
                self.logger.error("LTSpice processing failed")
                return None
            asc_path, image_path = result
            self.logger.info(f"LTSpice processing successful. ASC: {asc_path}, Image: {image_path}")
            return asc_path, image_path
        except Exception as e:
            self.logger.error(f"Unexpected error in LTSpice processing: {str(e)}")
            return None

    def get_output_paths(self, prompt_id: int, iteration: int) -> Tuple[str, str]:
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
