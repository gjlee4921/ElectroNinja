# electroninja/utils/async_workers.py

import os
import logging
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger('electroninja')

class LLMWorker(QThread):
    """Worker thread for asynchronous LLM calls"""

    resultReady = pyqtSignal(str)

    def __init__(self, func, prompt):
        super().__init__()
        self.func = func
        self.prompt = prompt

    def run(self):
        logger.info("LLMWorker: Sending prompt to LLM...")
        try:
            result = self.func(self.prompt)
            logger.info("LLMWorker: Received response from LLM.")
            self.resultReady.emit(result)
        except Exception as e:
            logger.error(f"LLMWorker error: {str(e)}")
            self.resultReady.emit(f"Error: {str(e)}")

class CircuitProcessingWorker(QThread):
    """Worker thread for asynchronous circuit processing"""

    # Signal for status updates during processing
    statusUpdate = pyqtSignal(str)
    
    # Signal for when the result is ready
    resultReady = pyqtSignal(dict)
    
    # Signal specifically for when ASC code is generated
    ascCodeGenerated = pyqtSignal(str)
    
    # Signal for when a circuit image is generated
    imageGenerated = pyqtSignal(str)

    def __init__(self, feedback_manager, request, examples=None, prompt_id=1):
        super().__init__()
        self.feedback_manager = feedback_manager
        self.request = request
        self.examples = examples
        self.prompt_id = prompt_id

    def run(self):
        """Process the circuit request asynchronously"""
        logger.info(f"CircuitProcessingWorker: Processing request: {self.request}")
        
        try:
            # Define a callback to emit status updates
            def status_callback(message):
                logger.info(f"Status update: {message}")
                self.statusUpdate.emit(message)
            
            # Process the request
            result = self.feedback_manager.process_request(
                self.request,
                prompt_id=self.prompt_id,
                examples=self.examples,
                status_callback=status_callback
            )
            
            logger.info(f"Result keys: {result.keys() if result else 'None'}")
            
            # Emit signals for UI updates
            if "asc_code" in result:
                logger.info(f"ASC code found: {len(result['asc_code'])} chars")
                self.ascCodeGenerated.emit(result["asc_code"])
                
            if "image_path" in result and result["image_path"]:
                logger.info(f"Image path found: {result['image_path']}")
                if os.path.exists(result["image_path"]):
                    logger.info(f"Image file exists: {os.path.getsize(result['image_path'])} bytes")
                    self.imageGenerated.emit(result["image_path"])
                else:
                    logger.warning(f"Image file doesn't exist: {result['image_path']}")
            
            # Emit the final result
            self.resultReady.emit(result)
            
        except Exception as e:
            logger.error(f"CircuitProcessingWorker error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.resultReady.emit({
                "success": False,
                "error": str(e)
            })