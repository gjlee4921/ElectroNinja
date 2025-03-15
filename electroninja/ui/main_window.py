# electroninja/ui/main_window.py
import logging
import asyncio
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication
from electroninja.ui.components.top_bar import TopBar
from electroninja.ui.panels.left_panel import LeftPanel
from electroninja.ui.panels.middle_panel import MiddlePanel
from electroninja.ui.panels.right_panel import RightPanel

# Import backend modules and provider
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.backend.request_evaluator import RequestEvaluator
from electroninja.backend.chat_response_generator import ChatResponseGenerator
from electroninja.backend.circuit_generator import CircuitGenerator
from electroninja.backend.ltspice_manager import LTSpiceManager
from electroninja.backend.vision_processor import VisionProcessor
from electroninja.llm.vector_store import VectorStore

# Import our async pipeline worker
from electroninja.ui.workers.pipeline_worker import run_pipeline

logger = logging.getLogger('electroninja')

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ElectroNinja")
        self.resize(1200, 800)
        self.init_backend()
        self.initUI()

    def init_backend(self):
        # Initialize backend provider and modules.
        self.openai_provider = OpenAIProvider()
        self.evaluator = RequestEvaluator(self.openai_provider)
        self.chat_generator = ChatResponseGenerator(self.openai_provider)
        vector_store = VectorStore()
        self.circuit_generator = CircuitGenerator(self.openai_provider, vector_store)
        self.ltspice_manager = LTSpiceManager()
        self.vision_processor = VisionProcessor()
        self.prompt_id = 1   # For simplicity, we use prompt ID 1.
        self.max_iterations = 3  # Number of refinement iterations.

    def initUI(self):
        # Create the central widget and set the main layout.
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Bar
        self.top_bar = TopBar(self)
        main_layout.addWidget(self.top_bar)

        # Main content area (Left, Middle, Right Panels)
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

        # Connect signal from the right panel (user chat input) to start processing.
        self.right_panel.messageSent.connect(self.handle_user_message)

    def handle_user_message(self, message):
        # Add the user message as a chat bubble.
        self.right_panel.chat_panel.add_message(message, is_user=True)
        # Set processing flag (to disable new inputs until done).
        self.right_panel.set_processing(True)
        # Clear previous code and image.
        self.left_panel.clear_code()
        self.middle_panel.clear_image()

        # Dictionary of callback functions for UI updates.
        update_callbacks = {
            "evaluation_done": self.on_evaluation_done,
            "non_circuit_response": self.on_non_circuit_response,
            "initial_chat_response": self.on_initial_chat_response,
            "asc_code_generated": self.on_asc_code_generated,
            "ltspice_processed": self.on_ltspice_processed,
            "vision_feedback": self.on_vision_feedback,
            "feedback_chat_response": self.on_feedback_chat_response,
            "asc_refined": self.on_asc_refined,
            "final_complete_chat_response": self.on_final_complete_chat_response,
            "iteration_update": self.on_iteration_update,
            "processing_finished": self.on_processing_finished,
        }

        # Launch the asynchronous pipeline.
        asyncio.create_task(run_pipeline(
            user_message=message,
            evaluator=self.evaluator,
            chat_generator=self.chat_generator,
            circuit_generator=self.circuit_generator,
            ltspice_manager=self.ltspice_manager,
            vision_processor=self.vision_processor,
            prompt_id=self.prompt_id,
            max_iterations=self.max_iterations,
            update_callbacks=update_callbacks
        ))

    # --- Callback Handlers ---
    def on_evaluation_done(self, is_circuit):
        logger.info(f"Evaluation completed: is_circuit={is_circuit}")

    def on_non_circuit_response(self, response):
        self.right_panel.receive_message(response)

    def on_initial_chat_response(self, response):
        self.right_panel.receive_message_with_type(response, "initial")

    def on_asc_code_generated(self, asc_code):
        self.left_panel.set_code(asc_code, animated=True)

    def on_ltspice_processed(self, result):
        # Expected result is a tuple: (asc_path, image_path, iteration)
        if result and len(result) == 3:
            asc_path, image_path, iteration = result
            self.left_panel.set_iteration(iteration)
            self.middle_panel.set_circuit_image(image_path, iteration)

    def on_vision_feedback(self, feedback):
        logger.info(f"Vision Feedback: {feedback}")

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
    import sys
    import asyncio
    try:
        from qasync import QEventLoop
    except ImportError:
        raise ImportError("Please install qasync to run the async event loop integration: pip install qasync")
    
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    with loop:
        loop.run_forever()
