#async_workers.py

from PyQt5.QtCore import QThread, pyqtSignal
import logging

logger = logging.getLogger('electroninja')

class LLMWorker(QThread):
    """Worker thread for asynchronous LLM calls"""

    resultReady = pyqtSignal(str)

    def init(self, func, prompt):
        super().init()
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

    statusUpdate = pyqtSignal(str)
    resultReady = pyqtSignal(dict)

    def init(self, feedback_manager, request, examples=None):
        super().init()
        self.feedback_manager = feedback_manager
        self.request = request
        self.examples = examples

    def run(self):
        logger.info(f"CircuitProcessingWorker: Processing request: {self.request}")
        try:
            result = self.feedback_manager.process_request(
                self.request,
                examples=self.examples,
                status_callback=lambda msg: self.statusUpdate.emit(msg)
            )
            self.resultReady.emit(result)
        except Exception as e:
            logger.error(f"CircuitProcessingWorker error: {str(e)}")
            self.resultReady.emit({
                "success": False,
                "error": str(e)
            })