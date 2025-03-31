# electroninja/ui/main_window.py
import logging
import asyncio
import concurrent.futures
import os
import traceback
import functools

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PyQt5.QtCore import QTimer

from electroninja.ui.components.top_bar import TopBar
from electroninja.ui.panels.left_panel import LeftPanel
from electroninja.ui.panels.middle_panel import MiddlePanel
from electroninja.ui.panels.right_panel import RightPanel

from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.backend.request_evaluator import RequestEvaluator
from electroninja.backend.chat_response_generator import ChatResponseGenerator
from electroninja.backend.circuit_generator import CircuitGenerator
from electroninja.backend.ltspice_manager import LTSpiceManager
from electroninja.backend.vision_processor import VisionProcessor
from electroninja.llm.vector_store import VectorStore
from electroninja.backend.create_description import CreateDescription

from electroninja.ui.workers.pipeline_worker import run_pipeline

logger = logging.getLogger('electroninja')

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ElectroNinja")
        self.resize(1200, 800)
        self.user_requests = {}
        self.current_prompt_id = 1
        self.active_tasks = set()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, 
                                                             thread_name_prefix="electroninja_worker")
        self.init_backend()
        self.initUI()

    def init_backend(self):
        self.openai_provider = OpenAIProvider()
        self.evaluator = RequestEvaluator(self.openai_provider)
        self.chat_generator = ChatResponseGenerator(self.openai_provider)
        vector_store = VectorStore()
        self.circuit_generator = CircuitGenerator(self.openai_provider, vector_store)
        self.ltspice_manager = LTSpiceManager()
        self.vision_processor = VisionProcessor()
        self.description_creator = CreateDescription(self.openai_provider)
        self.max_iterations = 3
        os.makedirs(os.path.join("data", "output"), exist_ok=True)

    def initUI(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.top_bar = TopBar(self)
        main_layout.addWidget(self.top_bar)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        self.left_panel = LeftPanel(self)
        content_layout.addWidget(self.left_panel, 2)
        self.middle_panel = MiddlePanel(self)
        content_layout.addWidget(self.middle_panel, 3)
        self.right_panel = RightPanel(self)
        content_layout.addWidget(self.right_panel, 2)
        main_layout.addLayout(content_layout)
        self.setCentralWidget(central_widget)
        self.right_panel.messageSent.connect(self.handle_user_message)

    def create_tracked_task(self, coro):
        task = asyncio.create_task(coro)
        self.active_tasks.add(task)
        task.add_done_callback(lambda t: self.active_tasks.discard(t))
        return task

    def closeEvent(self, event):
        for task in self.active_tasks:
            if not task.done():
                task.cancel()
        self.executor.shutdown(wait=False)
        super().closeEvent(event)

    def handle_user_message(self, message):
        self.right_panel.set_processing(True)
        request_number = len(self.user_requests) + 1
        self.user_requests[f"request{request_number}"] = message
        self.process_message_in_background(message, request_number)

    def process_message_in_background(self, message, request_number):
        async def background_task():
            try:
                # Evaluate the request.
                is_relevant = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.evaluator.is_circuit_related, message)
                if hasattr(self, "on_evaluation_done"):
                    self.on_evaluation_done(is_relevant)
                if is_relevant.strip().upper() == 'N':
                    response = await asyncio.get_event_loop().run_in_executor(
                        self.executor, self.chat_generator.generate_response, message)
                    self.right_panel.receive_message(response)
                    self.right_panel.set_processing(False)
                    return

                # For modification requests, load previous description and increment prompt ID.
                previous_description = None
                if request_number > 1:
                    previous_description = await asyncio.get_event_loop().run_in_executor(
                        self.executor, self.description_creator.load_description, self.current_prompt_id)
                    self.current_prompt_id += 1

                skip_eval = (request_number > 1)
                update_callbacks = {
                    "evaluation_done": self.on_evaluation_done,
                    "non_circuit_response": self.on_non_circuit_response,
                    "description_generated": self.on_description_generated,
                    "initial_chat_response": self.on_initial_chat_response,
                    "asc_code_generated": self.on_asc_code_generated,
                    "ltspice_processed": self.on_ltspice_processed,
                    "vision_feedback": self.on_vision_feedback,
                    "feedback_chat_response": self.on_feedback_chat_response,
                    "asc_refined": self.on_asc_refined,
                    "final_complete_chat_response": self.on_final_complete_chat_response,
                    "iteration_update": self.on_iteration_update,
                    "processing_finished": self.on_processing_finished
                }
                await run_pipeline(
                    user_message=message,
                    evaluator=self.evaluator,
                    chat_generator=self.chat_generator,
                    circuit_generator=self.circuit_generator,
                    ltspice_manager=self.ltspice_manager,
                    vision_processor=self.vision_processor,
                    prompt_id=self.current_prompt_id,
                    max_iterations=self.max_iterations,
                    update_callbacks=update_callbacks,
                    skip_evaluation=skip_eval,
                    executor=self.executor,
                    description_creator=self.description_creator,
                    previous_description=previous_description
                )
            except asyncio.CancelledError:
                self.right_panel.set_processing(False)
                raise
            except Exception as e:
                logger.error(f"Error in background task: {str(e)}")
                traceback.print_exc()
                self.right_panel.set_processing(False)
        self.create_tracked_task(background_task())

    # --- Callback Handlers ---
    def on_evaluation_done(self, result):
        logger.info(f"Evaluation done: {result}")

    def on_non_circuit_response(self, response):
        self.right_panel.receive_message(response)

    def on_description_generated(self, description):
        logger.info(f"Description generated: {description[:100]}...")

    def on_initial_chat_response(self, response):
        self.right_panel.receive_message_with_type(response, "initial")

    def on_asc_code_generated(self, asc_code):
        self.left_panel.set_code(asc_code, animated=True)

    def on_ltspice_processed(self, result):
        if result and len(result) == 3:
            asc_path, image_path, iteration = result
            self.left_panel.set_iteration(iteration)
            self.middle_panel.set_circuit_image(image_path, iteration)

    def on_vision_feedback(self, feedback):
        logger.info(f"Vision feedback: {feedback}")

    def on_feedback_chat_response(self, response):
        self.right_panel.receive_message_with_type(response, "refining")

    def on_asc_refined(self, refined_code):
        self.left_panel.set_code(refined_code, animated=True)

    def on_final_complete_chat_response(self, response):
        self.right_panel.receive_message_with_type(response, "complete")

    def on_iteration_update(self, iteration):
        self.left_panel.set_iteration(iteration)

    def on_processing_finished(self):
        self.right_panel.set_processing(False)

if __name__ == "__main__":
    import sys, asyncio
    try:
        from qasync import QEventLoop
    except ImportError:
        raise ImportError("Please install qasync: pip install qasync")
    
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    with loop:
        loop.run_forever()
