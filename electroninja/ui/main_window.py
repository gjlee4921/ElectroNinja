# electroninja/ui/main_window.py
import logging
import asyncio
import concurrent.futures
import os
import traceback
import functools
import shutil
from pathlib import Path

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PyQt5.QtCore import QTimer

from electroninja.config.settings import Config

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
        self.current_prompt_id = 1  # Start with prompt 1
        self.config = Config()
        self.ltspice_path = self.config.LTSPICE_PATH
        self.output_dir = self.config.OUTPUT_DIR
        if not os.path.exists(self.ltspice_path):
            logger.warning(f"LTSpice executable not found at '{self.ltspice_path}'")
        else:
            logger.info(f"LTSpice found at '{self.ltspice_path}'")
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
        self.clear_output_directory(self.output_dir)
        os.makedirs(os.path.join("data", "output"), exist_ok=True)

    def clear_output_directory(self, directory: str):
        """
        Removes the read-only attribute from all files in the directory (including subdirectories),
        then deletes all files and directories in the specified directory.
        """
        for root, dirs, files in os.walk(directory, topdown=False):
            # Remove read-only attribute and delete files
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # Remove read-only attribute for Windows
                    os.system(f'attrib -r "{file_path}"')
                    
                    # Make the file writable for other systems (like Linux)
                    os.chmod(file_path, 0o777)  # Remove read-only on Linux/Mac
                    
                    # Delete the file
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error while removing file {file_path}: {e}")

            # Remove read-only attribute and delete directories
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    # Remove read-only attribute for Windows
                    os.system(f'attrib -r "{dir_path}"')
                    
                    # Make the directory writable for other systems (like Linux)
                    os.chmod(dir_path, 0o777)  # Remove read-only on Linux/Mac
                    
                    # Delete the directory
                    shutil.rmtree(dir_path)
                except Exception as e:
                    print(f"Error while removing directory {dir_path}: {e}")

        print("Cleared output directory")

    # In main_window.py, inside the MainWindow class

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
        
        # Initialize left panel and connect the compile button signal
        self.left_panel = LeftPanel(self)
        self.left_panel.compile_button.clicked.connect(self.handle_compile_button)
        content_layout.addWidget(self.left_panel, 2)
        
        self.middle_panel = MiddlePanel(self)
        self.middle_panel.edit_button.clicked.connect(self.handle_edit_button)
        content_layout.addWidget(self.middle_panel, 3)
        self.right_panel = RightPanel(self)
        content_layout.addWidget(self.right_panel, 2)
        main_layout.addLayout(content_layout)
        self.setCentralWidget(central_widget)
        self.right_panel.messageSent.connect(self.handle_user_message)

    # New method to handle the compile button click
    def handle_compile_button(self):
        """
        Triggered when the user clicks the compile button in the left panel.
        It retrieves the code, processes it via LTSpice, and updates the UI.
        """
        self.right_panel.set_processing(True)
        # Disable the compile button (it will show as gray thanks to the stylesheet)
        self.left_panel.compile_button.setEnabled(False)
        code = self.left_panel.get_code()
        current_prompt = self.current_prompt_id  # use current prompt ID
        self.create_tracked_task(self.compile_code_background(code, current_prompt))

    def handle_edit_button(self):
        """
        Manually open the circuit from the main window's left panel in LTSpice
        and then show the resulting image in the middle panel.
        """
        import os
        import time
        import pygetwindow as gw
        import pyautogui
        import subprocess
        from PyQt5.QtWidgets import QMessageBox

        # The real left panel is in the main window
        main_window = self.window()
        left_panel = main_window.left_panel
        ltspice_path = self.ltspice_path

        circuit_text = left_panel.code_editor.toPlainText().strip()
        if not circuit_text:
            QMessageBox.warning(self, "Error", "No circuit code entered!")
            return

        # Save the .asc file as a temporary file
        temp_file_path = os.path.join(os.getcwd(), "ltspice_edit.asc")
        with open(temp_file_path, "w") as f:
            f.write(circuit_text)

        print(f"🔹 Temporary LTSpice file saved at: {temp_file_path}")

        # Try opening LTSpice
        try:
            ltspice_process = subprocess.Popen([ltspice_path, temp_file_path])
        except FileNotFoundError:
            QMessageBox.critical(self, "LTSpice Error", "LTSpice executable not found!")
            return

        print("🔹 LTSpice opened. Monitoring for exit...")

        # Monitor for "Save changes?" pop-up
        time.sleep(4)
        initial_len = len(gw.getWindowsWithTitle("LTspice"))
        while ltspice_process.poll() is None:
            time.sleep(0.5)
            windows = gw.getWindowsWithTitle("LTspice")
            if len(windows) > initial_len:
                print("Detected LTSpice save pop-up. Pressing 'Cancel'...")
                time.sleep(0.5)
                pyautogui.press("esc")
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 's')
                break
        
        with open(temp_file_path, "r") as f:
            asc_code = f.read()

        self.right_panel.set_processing(True)
        current_prompt = self.current_prompt_id  # use current prompt ID
        self.create_tracked_task(self.compile_code_background(asc_code, current_prompt))

        # Clean up
        try:
            os.remove(temp_file_path)
        except Exception as e:
            print(f"Error deleting temporary file: {e}")

    
    # New asynchronous method that runs the compile process in the background
    async def compile_code_background(self, code, prompt_id):
        try:
            # Process the ASC code using LTSpice (iteration 0)
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.ltspice_manager.process_circuit,
                code,
                prompt_id,
                0  # iteration set to 0
            )
            if result:
                asc_path, image_path = result
                # Update the left panel (code editor) and middle panel (circuit image)
                self.left_panel.set_code(code, animated=False)
                self.middle_panel.set_circuit_image(image_path, 0)

                # --- New: Create description from compiled image ---
                loop = asyncio.get_event_loop()
                description_future = loop.run_in_executor(
                    self.executor, self.vision_processor.create_description_from_compile, prompt_id
                )

                # --- New: Generate components file from the ASC code ---
                components_future = loop.run_in_executor(
                    self.executor, self.evaluator.list_components, prompt_id
                )

                # Wait for both operations to complete concurrently.
                description_result = await description_future
                components_result = await components_future

                logger.info(f"Description created from compile: {description_result}")
                logger.info(f"Components listed: {components_result}")
            else:
                self.right_panel.receive_message("Compile failed. Please check your code or LTSpice configuration.")
            
            # Increment the prompt ID so that the next compile or prompt uses a new folder.
            self.current_prompt_id += 1
        except Exception as e:
            logger.error(f"Error in compile_code_background: {e}")
            self.right_panel.receive_message("An error occurred during compile.")
        finally:
            self.right_panel.set_processing(False)
            # Re-enable the compile button, which now should appear in purple per the stylesheet.
            self.left_panel.compile_button.setEnabled(True)

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
        request_number = self.current_prompt_id
        self.user_requests[f"request{request_number}"] = message
        self.process_message_in_background(message, request_number)

    def process_message_in_background(self, message, request_number):
        async def background_task():
            try:
                # For modification requests (request_number > 1), load the previous description 
                # from the last prompt folder (current_prompt_id - 1).
                previous_description = None
                if request_number > 1:
                    previous_description = await asyncio.get_event_loop().run_in_executor(
                        self.executor, self.description_creator.load_description, self.current_prompt_id - 1)
                
                # Use the current prompt ID for this pipeline.
                current_id = self.current_prompt_id
                
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
                # Run the pipeline and capture its result.
                processed = await run_pipeline(
                    user_message=message,
                    evaluator=self.evaluator,
                    chat_generator=self.chat_generator,
                    circuit_generator=self.circuit_generator,
                    ltspice_manager=self.ltspice_manager,
                    vision_processor=self.vision_processor,
                    prompt_id=current_id,
                    max_iterations=self.max_iterations,
                    update_callbacks=update_callbacks,
                    not_first_eval=(request_number > 1),
                    executor=self.executor,
                    description_creator=self.description_creator,
                    previous_description=previous_description
                )
                
                # Only increment prompt_id if the pipeline processed a circuit-related request.
                if processed:
                    self.current_prompt_id += 1
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

    def on_iteration_update(self):
        pass

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
            self.middle_panel.set_circuit_image(image_path, iteration)

    def on_vision_feedback(self, feedback):
        logger.info(f"Vision feedback: {feedback}")

    def on_feedback_chat_response(self, response):
        self.right_panel.receive_message_with_type(response, "refining")

    def on_asc_refined(self, refined_code):
        self.left_panel.set_code(refined_code, animated=True)

    def on_final_complete_chat_response(self, response):
        self.right_panel.receive_message_with_type(response, "complete")

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
