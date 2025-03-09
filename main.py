import sys, os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, Qt, pyqtSlot, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# Import custom modules
from electroninja.gui.style import STYLE_SHEET, setup_fonts, COLORS
from electroninja.gui.top_bar import TopBar
from electroninja.gui.left_panel import LeftPanel
from electroninja.gui.middle_panel import MiddlePanel
from electroninja.gui.right_panel import RightPanel
from electroninja.llm.chat_manager import ChatManager, general, asc_generation_prompt, user_prompt, safety_for_agent
from electroninja.llm.vector_db import VectorDB

# Worker class for asynchronous LLM calls
class LLMWorker(QThread):
    resultReady = pyqtSignal(str)
    def __init__(self, func, prompt):
        super().__init__()
        self.func = func
        self.prompt = prompt
    def run(self):
        result = self.func(self.prompt)
        self.resultReady.emit(result)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ElectroNinja - Electrical Engineer Agent")
        self.setGeometry(100, 50, 1400, 800)  # Larger default size

        # Collapsed and expanded widths for the left panel
        self.left_panel_collapsed_width = 80
        self.left_panel_expanded_width = 0  # Calculated at runtime
        
        # Current circuit file and prompt
        self.current_circuit_file = None
        self.circuit_request_prompt = None  # Stores the latest circuit request
        
        # Initialize simulation process (if needed later)
        self.ltspice_process = None

        # Conversation history: only store outputs from o3-mini (ASC code attempts) and vision feedback.
        # Each entry will be a dict: {"attempt": <number>, "asc_code": "<code>"}.
        self.conversation_history = []
        self.attempt_counter = 0

        # Instantiate our ChatManager and VectorDB.
        self.chat_manager = ChatManager()
        self.vector_db = VectorDB()  # Ensure your DB is up and running.

        # Test mode: when True, print the constructed prompt instead of sending it.
        self.test_mode = True

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

        self.left_panel = LeftPanel(self)
        self.middle_panel = MiddlePanel(self)
        self.right_panel = RightPanel(self)

        self.left_panel.setSizePolicy(QWidget().sizePolicy())
        self.middle_panel.setSizePolicy(QWidget().sizePolicy())
        self.right_panel.setSizePolicy(QWidget().sizePolicy())

        self.left_panel.setMinimumWidth(self.left_panel_collapsed_width)
        self.left_panel.setMaximumWidth(300)

        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.middle_panel)
        self.main_layout.addWidget(self.right_panel)

        self.left_panel.toggleRequested.connect(self.on_left_panel_toggle)

    def connectSignals(self):
        self.right_panel.messageSent.connect(self.handle_message)
        self.left_panel.compile_button.clicked.connect(self.compile_circuit)
        self.middle_panel.edit_button.clicked.connect(self.edit_with_ltspice)

    def on_left_panel_toggle(self, is_expanding):
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
        animation = QPropertyAnimation(self.left_panel, b"maximumWidth")
        animation.setDuration(600)
        animation.setStartValue(start_width)
        animation.setEndValue(end_width)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.finished.connect(lambda: self.left_panel.setMaximumWidth(end_width))
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustPanelWidths()

    def build_prompt(self, user_request: str) -> str:
        """
        Constructs a prompt for the o3-mini model that includes the 3 most semantically similar
        circuit examples from the vector DB, then the user's request.
        """
        # Retrieve the top-3 examples from the vector database.
        results = self.vector_db.search(user_request, top_k=3)
        examples_text = ""
        for i, res in enumerate(results, start=1):
            desc = res["metadata"].get("description", "No description")
            asc_code = res["asc_code"]
            examples_text += f"Example {i}:\nDescription: {desc}\nASC Code:\n-----------------\n{asc_code}\n-----------------\n\n"
        
        prompt = (
            f"{general}\n\n"
            "Below are three examples of circuits similar to the user's request:\n\n"
            f"{examples_text}"
            f"User's request: {user_request}\n\n"
            "Now, based on the examples above, generate the complete .asc code for a circuit that meets the user's request.\n"
            "Your answer must contain only valid .asc code with no additional explanation."
        )
        return prompt

    @pyqtSlot(str)
    def handle_message(self, message):
        print(f"Received message: {message}")
        # The RightPanel already displays the user's message as a bubble.
        if any(kw in message.lower() for kw in ["circuit", "resistor", "capacitor", "oscillator", "filter"]):
            self.circuit_request_prompt = message
            print(f"Stored circuit prompt: {self.circuit_request_prompt}")
            self.attempt_counter += 1

            # Build the prompt with context from the vector DB.
            final_prompt = self.build_prompt(self.circuit_request_prompt)
            # For test mode, print the prompt.
            if self.test_mode:
                print("=== Prompt to o3-mini ===")
                print(final_prompt)
                # Disable test_mode for subsequent calls
                self.test_mode = False
            # Now call the o3-mini model using a worker.
            self.ascWorker = LLMWorker(self.chat_manager.get_asc_code, final_prompt)
            self.ascWorker.resultReady.connect(self.on_asc_code_ready)
            self.ascWorker.start()
        else:
            response = self.generate_response(message)
            self.right_panel.receive_message(response)

    def on_asc_code_ready(self, asc_code):
        if asc_code and asc_code != "N":
            self.left_panel.code_editor.setText(asc_code)
            self.conversation_history.append({
                "attempt": self.attempt_counter,
                "asc_code": asc_code
            })
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
            return "LTspice is a powerful circuit simulation tool. You can use the editor button to open your design in LTSpice when you're ready."
        elif "help" in text:
            return "I can help you design circuits, analyze components, or explain electrical concepts. Please describe what you're trying to build!"
        else:
            return "I'll analyze your request and help design the appropriate circuit. Could you provide more specific details about your requirements?"

    def compile_circuit(self):
        asc_code = self.left_panel.code_editor.toPlainText()
        if not asc_code.strip():
            self.right_panel.receive_message("Please enter some circuit code first!")
            return
        print("Compiling circuit code...")
        self.right_panel.receive_message("Circuit compiled successfully! You can see the result in the middle panel.")
        self.middle_panel.circuit_display.setText("Circuit preview would be displayed here")
        self.save_circuit()

    def save_circuit(self):
        if self.current_circuit_file is None:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_dir = f"output_{timestamp}"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            self.current_circuit_file = os.path.join(output_dir, "circuit.asc")
        with open(self.current_circuit_file, 'w') as f:
            f.write(self.left_panel.code_editor.toPlainText())
        self.right_panel.receive_message(f"Circuit saved to {self.current_circuit_file}")
        self.conversation_history.append({"role": "system", "content": f"Circuit saved to {self.current_circuit_file}"})

    def edit_with_ltspice(self):
        if not self.current_circuit_file:
            self.save_circuit()
        print(f"Opening circuit in LTSpice: {self.current_circuit_file}")
        self.right_panel.receive_message("Opening circuit in LTSpice. This would launch the external application in a real implementation.")
        self.conversation_history.append({"role": "system", "content": "Launching LTSpice with the current circuit."})

def main():
    app = QApplication(sys.argv)
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
