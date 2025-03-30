# electroninja/ui/main_window.py
import logging
import asyncio
import traceback
import functools
import concurrent.futures
import os
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PyQt5.QtCore import QTimer
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
from electroninja.backend.create_description import CreateDescription

# Import our async pipeline worker
from electroninja.ui.workers.pipeline_worker import run_pipeline

logger = logging.getLogger('electroninja')

# Wrapper class for OpenAIProvider to intercept API calls without printing
class LoggingOpenAIProvider:
    """
    Wrapper around OpenAIProvider that intercepts API calls.
    All printing has been removed per requirements.
    """
    def __init__(self, provider):
        self.provider = provider
        
        # Patch the provider's OpenAI client to intercept API calls
        if hasattr(self.provider, 'client'):
            original_chat_create = self.provider.client.chat.completions.create
            
            # Define wrapper that passes through with no printing
            def chat_create_wrapper(*args, **kwargs):
                # Make the API call without any printing
                response = original_chat_create(*args, **kwargs)
                return response
            
            # Replace the original method with our wrapper
            self.provider.client.chat.completions.create = chat_create_wrapper
    
    def __getattr__(self, name):
        """Pass through all method calls to the original provider."""
        return getattr(self.provider, name)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ElectroNinja")
        self.resize(1200, 800)
        # Dictionary to store successive user requests in the current session
        self.user_requests = {}
        # Used to determine which prompt folder to use
        self.current_prompt_id = 1
        # Track all active asyncio tasks for proper cleanup
        self.active_tasks = set()
        # Create a thread pool executor with a fixed number of workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, 
                                                             thread_name_prefix="electroninja_worker")
        # Initialize backend components
        self.init_backend()
        # Set up the user interface
        self.initUI()

    def init_backend(self):
        """
        Initialize all backend components with logging wrapper.
        """
        # Create OpenAI provider and wrap it with logging
        self.openai_provider = OpenAIProvider()
        self.logging_provider = LoggingOpenAIProvider(self.openai_provider)
        
        # Initialize components with the logging provider
        self.evaluator = RequestEvaluator(self.logging_provider)
        self.chat_generator = ChatResponseGenerator(self.logging_provider)
        vector_store = VectorStore()
        self.circuit_generator = CircuitGenerator(self.logging_provider, vector_store)
        self.ltspice_manager = LTSpiceManager()
        self.vision_processor = VisionProcessor()
        self.description_creator = CreateDescription(self.logging_provider)
        self.max_iterations = 3
        
        # Create output directory structure if it doesn't exist
        os.makedirs(os.path.join("data", "output"), exist_ok=True)

    def initUI(self):
        """
        Initialize the user interface with three panels.
        """
        # Create main widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add top bar with controls
        self.top_bar = TopBar(self)
        main_layout.addWidget(self.top_bar)

        # Create horizontal layout for the three panels
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        # Left panel for code display (2 parts width)
        self.left_panel = LeftPanel(self)
        content_layout.addWidget(self.left_panel, 2)

        # Middle panel for circuit image (3 parts width)
        self.middle_panel = MiddlePanel(self)
        content_layout.addWidget(self.middle_panel, 3)

        # Right panel for chat interface (2 parts width)
        self.right_panel = RightPanel(self)
        content_layout.addWidget(self.right_panel, 2)

        # Add the panels to the main layout
        main_layout.addLayout(content_layout)
        self.setCentralWidget(central_widget)

        # Connect the message signal from chat panel to our handler
        self.right_panel.messageSent.connect(self.handle_user_message)

    def closeEvent(self, event):
        """Handle window close event to clean up resources properly."""
        logger.info("Application closing, cleaning up resources...")
        
        # Cancel any running asyncio tasks
        for task in self.active_tasks:
            if not task.done():
                task.cancel()
        
        # Shutdown the thread executor
        self.executor.shutdown(wait=False)
        
        # Call the parent's closeEvent
        super().closeEvent(event)

    def create_tracked_task(self, coro):
        """Create and track asyncio tasks to ensure proper cleanup."""
        task = asyncio.create_task(coro)
        self.active_tasks.add(task)
        task.add_done_callback(lambda t: self.active_tasks.discard(t))
        return task

    def handle_user_message(self, message):
        """
        Process user messages and dispatch to appropriate handlers.
        NOTE: User message is already displayed in the chat panel by the RightPanel
        """
        # Disable further input while processing
        self.right_panel.set_processing(True)
        
        # For a new session, clear previous code/image
        if not self.user_requests:
            self.left_panel.clear_code()
            self.middle_panel.clear_image()

        # Add the new message to the history
        request_number = len(self.user_requests) + 1
        self.user_requests[f"request{request_number}"] = message

        # Start processing in a background task to keep UI responsive
        self.process_message_in_background(message, request_number)

    def process_message_in_background(self, message, request_number):
        """Process the user message in a background task to keep UI responsive"""
        
        # Create background task for processing
        async def background_task():
            try:
                # First, evaluate if the message is circuit-related
                is_relevant = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.evaluator.is_circuit_related,
                    message
                )
                
                if not is_relevant:
                    response = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        self.chat_generator.generate_response,
                        message
                    )
                    self.right_panel.receive_message(response)
                    self.right_panel.set_processing(False)
                    return

                # Load previous description if this is not the first request
                previous_description = None
                if request_number > 1:
                    previous_description = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        self.description_creator.load_description,
                        self.current_prompt_id - 1
                    )
                    # Increment prompt session ID for follow-up modifications
                    self.current_prompt_id += 1
                
                # Launch the pipeline for circuit processing
                # For follow-up requests, skip evaluation since we've already evaluated
                skip_eval = (request_number > 1)
                await run_pipeline(
                    user_message=message,
                    evaluator=self.evaluator,
                    chat_generator=self.chat_generator,
                    circuit_generator=self.circuit_generator,
                    ltspice_manager=self.ltspice_manager,
                    vision_processor=self.vision_processor,
                    prompt_id=self.current_prompt_id,
                    max_iterations=self.max_iterations,
                    update_callbacks={
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
                        "description_generated": self.on_description_generated,
                    },
                    skip_evaluation=skip_eval,
                    executor=self.executor,  # Pass the executor to the pipeline
                    description_creator=self.description_creator,
                    previous_description=previous_description
                )
            except asyncio.CancelledError:
                # Task was cancelled, do any cleanup here
                logger.info("Background task cancelled")
                self.right_panel.set_processing(False)
                raise
            except Exception as e:
                # Log any exceptions
                logger.error(f"Error in background task: {str(e)}")
                traceback.print_exc()
                # Make sure UI is restored
                self.right_panel.set_processing(False)
            
        # Start the background task with tracking
        self.create_tracked_task(background_task())

    # --- Callback Handlers ---
    def on_evaluation_done(self, is_circuit):
        """Callback: Request evaluation complete"""
        logger.info(f"Evaluation completed: is_circuit={is_circuit}")

    def on_non_circuit_response(self, response):
        """Callback: Non-circuit response generated"""
        self.right_panel.receive_message(response)

    def on_initial_chat_response(self, response):
        """Callback: Initial chat explanation generated"""
        self.right_panel.receive_message_with_type(response, "initial")

    def on_asc_code_generated(self, asc_code):
        """Callback: ASC circuit code generated"""
        self.left_panel.set_code(asc_code, animated=True)

    def on_ltspice_processed(self, result):
        """Callback: LTSpice processing complete"""
        if result and len(result) == 3:
            asc_path, image_path, iteration = result
            self.left_panel.set_iteration(iteration)
            self.middle_panel.set_circuit_image(image_path, iteration)

    def on_vision_feedback(self, feedback):
        """Callback: Vision analysis feedback received"""
        logger.info(f"Vision Feedback: {feedback}")

    def on_feedback_chat_response(self, response):
        """Callback: Feedback chat response for refinement"""
        self.right_panel.receive_message_with_type(response, "refining")

    def on_asc_refined(self, refined_code):
        """Callback: Refined ASC code received"""
        self.left_panel.set_code(refined_code, animated=True)

    def on_final_complete_chat_response(self, response):
        """Callback: Final complete explanation generated"""
        self.right_panel.receive_message_with_type(response, "complete")

    def on_iteration_update(self, iteration):
        """Callback: Iteration counter updated"""
        self.left_panel.set_iteration(iteration)

    def on_description_generated(self, description):
        """Callback: Circuit description generated"""
        logger.info(f"Description generated: {description[:100]}...")

    def on_processing_finished(self):
        """Callback: All processing complete"""
        self.right_panel.set_processing(False)

if __name__ == "__main__":
    import sys
    import asyncio
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