# electroninja/ui/workers/pipeline_worker.py

from PyQt5.QtCore import QThread, pyqtSignal
import traceback
import logging
from threading import Thread

logger = logging.getLogger('electroninja')

class PipelineWorker(QThread):
    # Signals to update the UI during different stages
    evaluationDone = pyqtSignal(bool)
    nonCircuitResponse = pyqtSignal(str)
    initialChatResponse = pyqtSignal(str)
    ascCodeGenerated = pyqtSignal(str)
    ltspiceProcessed = pyqtSignal(object)  # Emits a tuple: (asc_path, image_path, iteration)
    visionFeedback = pyqtSignal(str)
    feedbackChatResponse = pyqtSignal(str)
    ascRefined = pyqtSignal(str)
    finalCompleteChatResponse = pyqtSignal(str)
    iterationUpdate = pyqtSignal(int)
    processingFinished = pyqtSignal()
    
    def __init__(self, user_message, evaluator, chat_generator, circuit_generator,
                 ltspice_manager, vision_processor, prompt_id=1, max_iterations=3, parent=None):
        super().__init__(parent)
        self.user_message = user_message
        self.evaluator = evaluator
        self.chat_generator = chat_generator
        self.circuit_generator = circuit_generator
        self.ltspice_manager = ltspice_manager
        self.vision_processor = vision_processor
        self.prompt_id = prompt_id
        self.max_iterations = max_iterations

    def run(self):
        try:
            # Step 1: Evaluate if the request is circuit-related.
            is_circuit = self.evaluator.is_circuit_related(self.user_message)
            self.evaluationDone.emit(is_circuit)
            if not is_circuit:
                # For non-circuit requests, generate a polite response.
                response = self.chat_generator.generate_response(self.user_message)
                self.nonCircuitResponse.emit(response)
                return

            # Step 2: Generate initial chat response and ASC code concurrently.
            chat_response_result = [None]
            asc_code_result = [None]

            def generate_chat():
                chat_response_result[0] = self.chat_generator.generate_response(self.user_message)
                self.initialChatResponse.emit(chat_response_result[0])

            def generate_asc():
                asc_code_result[0] = self.circuit_generator.generate_asc_code(self.user_message)
                self.ascCodeGenerated.emit(asc_code_result[0])

            chat_thread = Thread(target=generate_chat)
            asc_thread = Thread(target=generate_asc)
            chat_thread.start()
            asc_thread.start()
            chat_thread.join()
            asc_thread.join()

            # Step 3: Process LTSpice for iteration 0.
            ltspice_result = self.ltspice_manager.process_circuit(asc_code_result[0], prompt_id=self.prompt_id, iteration=0)
            if ltspice_result:
                asc_path, image_path = ltspice_result
                self.ltspiceProcessed.emit((asc_path, image_path, 0))
            else:
                logger.error("LTSpice processing failed at iteration 0")
                self.ltspiceProcessed.emit((None, None, 0))
                return

            # Step 4: Get vision feedback for iteration 0.
            vision_result = self.vision_processor.analyze_circuit_image(image_path, self.user_message)
            self.visionFeedback.emit(vision_result)
            if vision_result.strip() == 'Y':
                complete_response = self.chat_generator.generate_response("Your circuit is complete!")
                self.finalCompleteChatResponse.emit(complete_response)
                return

            # Step 5: Iterative refinement loop.
            history = [{"asc_code": asc_code_result[0], "vision_feedback": vision_result, "iteration": 0}]
            iteration = 1
            while iteration < self.max_iterations:
                self.iterationUpdate.emit(iteration)
                feedback_response = self.chat_generator.generate_feedback_response(vision_result)
                self.feedbackChatResponse.emit(feedback_response)
                refined_code = self.circuit_generator.refine_asc_code(self.user_message, history)
                self.ascRefined.emit(refined_code)
                ltspice_result = self.ltspice_manager.process_circuit(refined_code, prompt_id=self.prompt_id, iteration=iteration)
                if ltspice_result:
                    asc_path, image_path = ltspice_result
                    self.ltspiceProcessed.emit((asc_path, image_path, iteration))
                else:
                    logger.error(f"LTSpice processing failed at iteration {iteration}")
                    self.ltspiceProcessed.emit((None, None, iteration))
                    break
                vision_result = self.vision_processor.analyze_circuit_image(image_path, self.user_message)
                self.visionFeedback.emit(vision_result)
                history.append({"asc_code": refined_code, "vision_feedback": vision_result, "iteration": iteration})
                if vision_result.strip() == 'Y':
                    complete_response = self.chat_generator.generate_response("Your circuit is complete!")
                    self.finalCompleteChatResponse.emit(complete_response)
                    break
                iteration += 1
        except Exception as e:
            logger.error("Exception in PipelineWorker: " + str(e))
            traceback.print_exc()
        finally:
            self.processingFinished.emit()
