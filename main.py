import sys, os, datetime, time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
)
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

        self.left_panel = LeftPanel(self)
        self.middle_panel = MiddlePanel(self)
        self.right_panel = RightPanel(self)

        self.left_panel_collapsed_width = 80
        self.left_panel_expanded_width = 0

        self.current_circuit_file = None
        self.circuit_request_prompt = None
        self.ltspice_process = None
        self.conversation_history = []
        self.attempt_counter = 0

        self.chat_manager = ChatManager()
        self.vector_db = VectorDB()
        # Load saved FAISS index and metadata (if available)
        print("Loading FAISS index and metadata...")
        self.vector_db.load_index("faiss_index.bin", "metadata_list.pkl")
        print("FAISS index loaded.")

        # For debugging: print prompt before sending to o3-mini.
        self.always_print_prompt = True

        self.left_panel.imageGenerated.connect(self.middle_panel.set_circuit_image)

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

        # Set size policies and initial widths
        self.left_panel.setMinimumWidth(self.left_panel_collapsed_width)
        self.left_panel.setMaximumWidth(300)

        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.middle_panel)
        self.main_layout.addWidget(self.right_panel)

        self.left_panel.toggleRequested.connect(self.on_left_panel_toggle)
        # Connect the left panel's imageGenerated signal to update the middle panel's image
        self.left_panel.imageGenerated.connect(self.middle_panel.set_circuit_image)
        print("UI initialized.")

    def connectSignals(self):
        self.right_panel.messageSent.connect(self.handle_message)
        # self.left_panel.compile_button.clicked.connect(self.compile_circuit)
        self.middle_panel.edit_button.clicked.connect(self.edit_with_ltspice)
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

    def build_prompt(self, user_request: str) -> str:
        print("Building prompt from user request and vector DB examples...")
        # Retrieve top 3 examples from the FAISS vector DB.
        results = self.vector_db.search(user_request, top_k=3)
        examples_text = ""
        for i, res in enumerate(results, start=1):
            desc = res["metadata"].get("description", "No description")
            asc_code = res["asc_code"]
            examples_text += (
                f"Example {i}:\n"
                f"Description: {desc}\n"
                "ASC Code:\n-----------------\n"
                f"{asc_code}\n-----------------\n\n"
            )
        prompt = (
            f"{general}\n\n"
            "Below are three examples of circuits similar to the user's request:\n\n"
            f"{examples_text}"
            f"User's request: {user_request}\n\n"
            "Now, based on the examples above, generate the complete .asc code for a circuit that meets the user's request.\n"
            "Your answer must contain only valid .asc code with no additional explanation."
        )
        print("Prompt built.")
        return prompt

    @pyqtSlot(str)
    def handle_message(self, message):
        print(f"Received message: {message}")
        if any(kw in message.lower() for kw in ["circuit", "resistor", "capacitor", "oscillator", "filter"]):
            self.circuit_request_prompt = message
            print(f"Stored circuit prompt: {self.circuit_request_prompt}")
            self.attempt_counter += 1

            # Build final prompt using examples from the vector DB
            final_prompt = self.build_prompt(self.circuit_request_prompt)
            print("=== Prompt to o3-mini ===")
            print(final_prompt)

            # Call o3-mini for ASC code generation.
            self.ascWorker = LLMWorker(self.chat_manager.get_asc_code, final_prompt)
            self.ascWorker.resultReady.connect(self.on_asc_code_ready)
            self.ascWorker.start()

            # Also call 4o-mini for a friendly chat response.
            self.chatWorker = LLMWorker(self.chat_manager.get_chat_response, message)
            self.chatWorker.resultReady.connect(lambda response: self.right_panel.receive_message(response))
            self.chatWorker.start()
        else:
            response = self.generate_response(message)
            self.right_panel.receive_message(response)

    def on_asc_code_ready(self, asc_code):
        print("ASC code generated by o3-mini:")
        print(asc_code)
        if asc_code and asc_code != "N":
            # Put generated code in left panel
            self.left_panel.code_editor.setText(asc_code)
            self.conversation_history.append({
                "attempt": self.attempt_counter,
                "asc_code": asc_code
            })
            # Save the circuit to a file and run the LTSpice process
            print("Saving generated ASC code to file...")
            self.save_circuit()
            # Use a slight delay to ensure the file is written before processing
            print("Waiting a moment before launching LTSpice...")
            QThread.sleep(1)
            print("Launching LTSpice processing...")
            self.run_ltspice_process()
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

    # def compile_circuit(self):
    #     asc_code = self.left_panel.code_editor.toPlainText()
    #     if not asc_code.strip():
    #         self.right_panel.receive_message("Please enter some circuit code first!")
    #         return
    #     print("Compiling circuit code...")
    #     self.right_panel.receive_message("Circuit compiled successfully! You can see the result in the middle panel.")
    #     self.middle_panel.circuit_display.setText("Circuit preview would be displayed here")
        # self.save_circuit()

    # def save_circuit(self):
    #     if self.current_circuit_file is None:
    #         import datetime
    #         timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    #         output_dir = f"output_{timestamp}"
    #         if not os.path.exists(output_dir):
    #             os.makedirs(output_dir)
    #         self.current_circuit_file = os.path.join(output_dir, "circuit.asc")
    #     with open(self.current_circuit_file, 'w') as f:
    #         f.write(self.left_panel.code_editor.toPlainText())
    #     self.right_panel.receive_message(f"Circuit saved to {self.current_circuit_file}")
    #     self.conversation_history.append({"role": "system", "content": f"Circuit saved to {self.current_circuit_file}"})

    def run_ltspice_process(self):
        """Calls circuit_saver with the current ASC file to run LTSpice and update the UI with the screenshot."""
        print("Running LTSpice process via circuit_saver...")
        from electroninja.circuits.circuit_saver import circuit_saver
        result = circuit_saver(self.current_circuit_file)
        if result:
            asc_path, png_file = result
            print("LTSpice processing finished. Checking updated files...")
            # Update left panel with the possibly modified ASC code from LTSpice
            if os.path.exists(asc_path):
                with open(asc_path, "r") as f:
                    updated_circuit_text = f.read()
                print("Updating left panel with LTSpice-modified ASC code.")
                self.left_panel.code_editor.setText(updated_circuit_text)
            # Emit signal so that middle panel displays the screenshot
            if png_file and os.path.exists(png_file):
                print(f"Emitting imageGenerated signal with PNG file: {png_file}")
                self.left_panel.imageGenerated.emit(png_file)
            else:
                print("PNG file not found after LTSpice processing.")
        else:
            self.right_panel.receive_message("Error: LTSpice processing failed.")
            print("Error: LTSpice processing failed.")

    def edit_with_ltspice(self):
        """Optional manual trigger to run the LTSpice process."""
        if not self.current_circuit_file:
            self.save_circuit()
        self.right_panel.receive_message("Opening circuit in LTSpice. Please wait while the schematic is processed.")
        print("Manual trigger: Running LTSpice process...")
        self.run_ltspice_process()

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
