import sys, os, time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, Qt, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# Import custom modules
from electroninja.gui.style import STYLE_SHEET, setup_fonts, COLORS
from electroninja.gui.top_bar import TopBar
from electroninja.gui.left_panel import LeftPanel
from electroninja.gui.middle_panel import MiddlePanel
from electroninja.gui.right_panel import RightPanel
from electroninja.llm.chat_manager import ChatManager, general, asc_generation_prompt, user_prompt, safety_for_agent
from electroninja.llm.vector_db import VectorDB
from electroninja.llm.vision import VisionManager

# Worker class for asynchronous LLM calls
class LLMWorker(QThread):
    resultReady = pyqtSignal(str)
    def __init__(self, func, prompt):
        super().__init__()
        self.func = func
        self.prompt = prompt
    def run(self):
        print("LLMWorker: Sending prompt to LLM...")
        result = self.func(self.prompt)
        print("LLMWorker: Received response from LLM.")
        self.resultReady.emit(result)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ElectroNinja - Electrical Engineer Agent")
        self.setGeometry(100, 50, 1400, 800)

        # Panel widths
        self.left_panel_collapsed_width = 80
        self.left_panel_expanded_width = 0

        # Circuit / LLM states
        self.current_circuit_file = None
        self.circuit_request_prompt = None
        self.conversation_history = []  # Stores ASC attempts and vision feedback
        self.attempt_counter = 0
        self.max_iterations = 5
        
        self.left_panel = LeftPanel(self)
        self.middle_panel = MiddlePanel(self)
        self.right_panel = RightPanel(self)

        # Initialize managers
        self.chat_manager = ChatManager()
        self.vector_db = VectorDB()
        print("Loading FAISS index and metadata...")
        self.vector_db.load_index("faiss_index.bin", "metadata_list.pkl")
        print("FAISS index loaded.")

        self.vision_manager = VisionManager(model="gpt-4o-mini")
        self.always_print_prompt = True

        self.initUI()
        self.connectSignals()
        self.adjustPanelWidths()

    def initUI(self):
        if 'setup_fonts' in globals():
            setup_fonts(QApplication.instance())
        self.setStyleSheet(STYLE_SHEET)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_vlayout = QVBoxLayout(central_widget)
        main_vlayout.setContentsMargins(10, 10, 10, 10)
        main_vlayout.setSpacing(10)

        self.top_bar = TopBar(self)
        main_vlayout.addWidget(self.top_bar)

        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(10)
        main_vlayout.addLayout(self.main_layout)


        self.left_panel.setMinimumWidth(self.left_panel_collapsed_width)
        self.left_panel.setMaximumWidth(300)

        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.middle_panel)
        self.main_layout.addWidget(self.right_panel)

        # Connect signals: When the left panel toggles or emits an image, update the UI.
        self.left_panel.toggleRequested.connect(self.on_left_panel_toggle)
        self.left_panel.imageGenerated.connect(self.middle_panel.set_circuit_image)
        print("UI initialized.")

    def connectSignals(self):
        self.right_panel.messageSent.connect(self.handle_message)
        self.left_panel.compile_button.clicked.connect(self.compile_circuit)
        print("Signals connected.")

    def on_left_panel_toggle(self, is_expanding):
        print(f"Left panel toggle requested. Expanding: {is_expanding}")
        if is_expanding:
            current_width = self.left_panel.maximumWidth()
            self.adjustPanelWidths()
            self.left_panel.showCodeEditor()
            self.animate_left_panel(current_width, self.left_panel_expanded_width)
        else:
            current_width = self.left_panel.maximumWidth()
            self.animate_left_panel(current_width, self.left_panel_collapsed_width)
            self.left_panel.hideCodeEditor()

    def animate_left_panel(self, start_width, end_width):
        print(f"Animating left panel from {start_width} to {end_width}")
        animation = QPropertyAnimation(self.left_panel, b"maximumWidth")
        animation.setDuration(600)
        animation.setStartValue(start_width)
        animation.setEndValue(end_width)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.finished.connect(lambda: print("Left panel animation complete."))
        animation.start()
        self.current_animation = animation

    def adjustPanelWidths(self):
        total_width = self.width() - 40
        left_width = int(total_width * 0.22)
        right_width = int(total_width * 0.28)
        self.left_panel_expanded_width = left_width
        if self.left_panel.toggle_button.isChecked():
            self.left_panel.setMaximumWidth(left_width)
        else:
            self.left_panel.setMaximumWidth(self.left_panel_collapsed_width)
        self.right_panel.setFixedWidth(right_width)
        print(f"Panel widths adjusted: Left: {left_width}, Right: {right_width}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustPanelWidths()

    def build_initial_prompt(self, user_request: str) -> str:
        print("Building initial prompt using RAG from the vector DB...")
        results = self.vector_db.search(user_request, top_k=3)
        examples_text = ""
        for i, res in enumerate(results, start=1):
            desc = res["metadata"].get("description", "No description")
            asc_code = res["asc_code"]
            examples_text += (
                f"Example {i}:\nDescription: {desc}\nASC Code:\n-----------------\n{asc_code}\n-----------------\n\n"
            )
        prompt = (
            f"{general}\n\n"
            "Below are three examples of circuits similar to the user's request:\n\n"
            f"{examples_text}"
            f"User's request: {user_request}\n\n"
            "Now, based on the examples above, generate the complete .asc code for a circuit that meets the user's request.\n"
            "Your answer must contain only valid .asc code with no additional explanation."
        )
        print("Initial prompt built.")
        return prompt

    def build_refinement_prompt(self) -> str:
        prompt = "Below are previous attempts and feedback:\n\n"
        for item in self.conversation_history:
            if "asc_code" in item:
                prompt += f"Attempt {item.get('attempt', item.get('iteration', '?'))} ASC code:\n{item['asc_code']}\n\n"
            if "vision_feedback" in item:
                prompt += f"Vision feedback (Iteration {item.get('iteration','?')}): {item['vision_feedback']}\n\n"
        prompt += f"Original user's request: {self.circuit_request_prompt}\n\n"
        prompt += (
            "Based on the above attempts and feedback, please provide a revised complete .asc code "
            "for a circuit that meets the original user's request. "
            "Your answer must contain only valid .asc code with no additional explanation."
        )
        print("Refinement prompt built:")
        print(prompt)
        return prompt

    @pyqtSlot(str)
    def handle_message(self, message):
        print(f"Received message: {message}")
        if any(kw in message.lower() for kw in ["circuit", "resistor", "capacitor", "oscillator", "filter"]):
            self.circuit_request_prompt = message
            print(f"Stored circuit prompt: {self.circuit_request_prompt}")
            self.attempt_counter += 1

            final_prompt = self.build_initial_prompt(self.circuit_request_prompt)
            print("=== Prompt to o3-mini ===")
            print(final_prompt)

            self.ascWorker = LLMWorker(self.chat_manager.get_asc_code, final_prompt)
            self.ascWorker.resultReady.connect(self.on_asc_code_ready)
            self.ascWorker.start()

            self.chatWorker = LLMWorker(self.chat_manager.get_chat_response, message)
            self.chatWorker.resultReady.connect(lambda response: self.right_panel.receive_message(response))
            self.chatWorker.start()
        else:
            response = self.generate_response(message)
            self.right_panel.receive_message(response)

    def on_asc_code_ready(self, asc_code):
        print("Initial ASC code generated by o3-mini:")
        print(asc_code)
        if asc_code and asc_code != "N":
            self.left_panel.code_editor.setText(asc_code)
            self.conversation_history.append({"attempt": self.attempt_counter, "asc_code": asc_code})
            print("Saving generated ASC code to file...")
            self.save_circuit()
            print("Waiting a moment before launching LTSpice for the first evaluation...")
            QThread.sleep(1)
            print("Launching LTSpice processing for initial evaluation...")
            self.run_feedback_loop(iteration=1)
        else:
            self.left_panel.code_editor.setText("")
            self.conversation_history.append({
                "attempt": self.attempt_counter,
                "asc_code": "No valid ASC code generated; query deemed irrelevant."
            })

    def generate_response(self, message):
        text = message.lower()
        if "hello" in text or "hi" in text:
            return "Hello! I'm ElectroNinja. How can I help with your circuit design?"
        elif "ltspice" in text:
            return "LTSpice is a powerful circuit simulation tool. You can use the editor button to open your design in LTSpice when you're ready."
        elif "help" in text:
            return "I can help you design circuits, analyze components, or explain electrical concepts. Please describe what you're trying to build!"
        else:
            return "I'll analyze your request and help design the appropriate circuit. Could you provide more specific details about your requirements?"

    def compile_circuit(self):
        asc_code = self.left_panel.code_editor.toPlainText()
        if not asc_code.strip():
            self.right_panel.receive_message("Please enter some circuit code first!")
            return
        print("Compiling circuit code manually...")
        self.right_panel.receive_message("Circuit compiled successfully! You can see the result in the middle panel.")
        self.save_circuit()

    def save_circuit(self):
        output_dir = os.path.join(os.getcwd(), "data", "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        self.current_circuit_file = os.path.join(output_dir, "circuit.asc")
        with open(self.current_circuit_file, 'w', encoding='utf-8') as f:
            f.write(self.left_panel.code_editor.toPlainText())
        print(f"Circuit saved to {self.current_circuit_file}")
        self.right_panel.receive_message(f"Circuit saved to {self.current_circuit_file}")
        self.conversation_history.append({
            "role": "system",
            "content": f"Circuit saved to {self.current_circuit_file}"
        })

    def run_feedback_loop(self, iteration):
        print(f"Starting feedback loop, iteration {iteration}...")
        from electroninja.circuits.circuit_saver import circuit_saver
        result = circuit_saver(self.current_circuit_file)
        if result:
            asc_path, png_file = result
            print("LTSpice processing finished. Checking updated files...")
            # Update left panel with the latest ASC code regardless of verification
            if os.path.exists(asc_path):
                with open(asc_path, "r", encoding='utf-8', errors='replace') as f:
                    updated_circuit_text = f.read()
                print("Updating left panel with LTSpice-modified ASC code.")
                self.left_panel.code_editor.setText(updated_circuit_text)
            # Update middle panel with the latest circuit image
            if os.path.exists(png_file):
                print("Updating middle panel with new circuit screenshot.")
                self.middle_panel.set_circuit_image(png_file)
            # Always get vision feedback and update chat, even if circuit is not verified
            self.right_panel.receive_message("Analyzing circuit image with vision model...")
            vision_feedback = self.vision_manager.analyze_circuit_image(png_file, self.circuit_request_prompt)
            print(f"Vision feedback (Iteration {iteration}): {vision_feedback}")
            status_update = self.chat_manager.get_status_update(self.conversation_history, vision_feedback, iteration)
            self.right_panel.receive_message(status_update)
            self.conversation_history.append({"iteration": iteration, "vision_feedback": vision_feedback})
            print("=== Conversation History After This Iteration ===")
            for i, item in enumerate(self.conversation_history, start=1):
                print(f"Item {i}: {item}")
            print("=================================================")
            # Always update the left panel with the new ASC code (even if not verified)
            if os.path.exists(asc_path):
                with open(asc_path, "r", encoding='utf-8', errors='replace') as f:
                    current_code = f.read()
                self.left_panel.code_editor.setText(current_code)
            # Check if vision feedback indicates success (accept if it contains "y")
            if "y" in vision_feedback.strip().lower():
                self.right_panel.receive_message("Circuit verified successfully!")
                print("Circuit verified successfully by vision model.")
                self.print_final_history()
                return
            elif iteration >= self.max_iterations:
                failure_msg = self.chat_manager.get_chat_response("Circuit refinement failed after maximum iterations.")
                self.right_panel.receive_message(failure_msg)
                print("Maximum iterations reached. Circuit refinement failed.")
                self.print_final_history()
                return
            else:
                # Get revised ASC code based on conversation history and vision feedback
                refinement_prompt = self.chat_manager.refine_asc_code(self.conversation_history, self.circuit_request_prompt)
                self.right_panel.receive_message(f"Refining circuit (Iteration {iteration}) based on feedback...")
                print("Refinement prompt to o3-mini:")
                print(refinement_prompt)
                new_asc_code = self.chat_manager.get_asc_code(refinement_prompt)
                print(f"New ASC code from refinement (Iteration {iteration}):")
                print(new_asc_code)
                self.left_panel.code_editor.setText(new_asc_code)
                self.conversation_history.append({"iteration": iteration, "asc_code": new_asc_code})
                self.save_circuit()
                print("Waiting a moment before re-running LTSpice processing...")
                QThread.sleep(1)
                self.run_feedback_loop(iteration + 1)
        else:
            self.right_panel.receive_message("Error: LTSpice processing failed.")
            print("Error: LTSpice processing failed in feedback loop.")
            self.print_final_history()

    def print_final_history(self):
        print("=== FINAL CONVERSATION HISTORY ===")
        for i, item in enumerate(self.conversation_history, start=1):
            print(f"Item {i}: {item}")
        print("==================================")

    def edit_with_ltspice(self):
        if not self.current_circuit_file:
            self.save_circuit()
        self.right_panel.receive_message("Manual trigger: Running LTSpice processing for circuit refinement...")
        print("Manual trigger: Running LTSpice processing...")
        self.run_feedback_loop(iteration=1)

def main():
    app = QApplication(sys.argv)
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)
    window = MainWindow()
    window.show()
    print("ElectroNinja agent started.")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
