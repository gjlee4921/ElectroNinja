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
from electroninja.llm.chat_manager import ChatManager

# Worker class for asynchronous LLM calls
class LLMWorker(QThread):
    resultReady = pyqtSignal(str)  # will emit the result string
    
    def __init__(self, func, prompt):
        super().__init__()
        self.func = func  # function to run (e.g., chat_manager.get_chat_response)
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

        # Conversation history: list of messages (each as a dict)
        self.conversation_history = []  # e.g., {"role": "user"/"assistant", "content": "..."}

        # Instantiate our ChatManager (LLM integration)
        self.chat_manager = ChatManager()

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

        # Top bar
        self.top_bar = TopBar(self)
        main_vlayout.addWidget(self.top_bar)

        # Main horizontal layout for left, middle, right panels
        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(10)
        main_vlayout.addLayout(self.main_layout)

        # Create panels
        self.left_panel = LeftPanel(self)
        self.middle_panel = MiddlePanel(self)
        self.right_panel = RightPanel(self)

        # Assign size policies
        self.left_panel.setSizePolicy(QWidget().sizePolicy())  # For animation
        self.middle_panel.setSizePolicy(QWidget().sizePolicy())  # Expanding center
        self.right_panel.setSizePolicy(QWidget().sizePolicy())  # Fixed width

        # Initially, set the left panel so it starts collapsed
        self.left_panel.setMinimumWidth(self.left_panel_collapsed_width)
        self.left_panel.setMaximumWidth(300)  # Temporary; recalculated below

        # Add panels in order: left, middle, right
        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.middle_panel)
        self.main_layout.addWidget(self.right_panel)

        # Connect the toggle signal from the left panel
        self.left_panel.toggleRequested.connect(self.on_left_panel_toggle)

    def connectSignals(self):
        # When the user sends a message from the chat, handle it here.
        self.right_panel.messageSent.connect(self.handle_message)
        self.left_panel.compile_button.clicked.connect(self.compile_circuit)
        self.middle_panel.edit_button.clicked.connect(self.edit_with_ltspice)

    def on_left_panel_toggle(self, is_expanding):
        if is_expanding:
            current_width = self.left_panel.maximumWidth()
            self.adjustPanelWidths()  # Recalculate expanded width
            self.left_panel.showCodeEditor()
            self.animate_left_panel(current_width, self.left_panel_expanded_width)
        else:
            current_width = self.left_panel.maximumWidth()
            self.animate_left_panel(current_width, self.left_panel_collapsed_width)
            self.left_panel.hideCodeEditor()

    def animate_left_panel(self, start_width, end_width):
        animation = QPropertyAnimation(self.left_panel, b"maximumWidth")
        animation.setDuration(600)  # Smooth animation
        animation.setStartValue(start_width)
        animation.setEndValue(end_width)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.finished.connect(lambda: self.left_panel.setMaximumWidth(end_width))
        animation.start()
        self.current_animation = animation  # Prevent garbage collection

    def adjustPanelWidths(self):
        total_width = self.width() - 40  # Account for margins/spacings
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

    @pyqtSlot(str)
    def handle_message(self, message):
        print(f"Received message: {message}")
        # Immediately store the user's message in the conversation history.
        self.conversation_history.append({"role": "user", "content": message})
        
        # The RightPanel already displays the user's message as a bubble.
        # Now, if the message is circuit-related, proceed with LLM calls.
        if any(kw in message.lower() for kw in ["circuit", "resistor", "capacitor", "oscillator", "filter"]):
            self.circuit_request_prompt = message
            print(f"Stored circuit prompt: {self.circuit_request_prompt}")

            # Start worker for chat response first (gpt-4o-mini)
            self.chatWorker = LLMWorker(self.chat_manager.get_chat_response, self.circuit_request_prompt)
            self.chatWorker.resultReady.connect(self.on_chat_response_ready)
            self.chatWorker.start()

            # Then start worker for asc code (o3-mini)
            self.ascWorker = LLMWorker(self.chat_manager.get_asc_code, self.circuit_request_prompt)
            self.ascWorker.resultReady.connect(self.on_asc_code_ready)
            self.ascWorker.start()
        else:
            response = self.generate_response(message)
            self.right_panel.receive_message(response)
            self.conversation_history.append({"role": "assistant", "content": response})

    def on_chat_response_ready(self, response):
        # Called when the friendly chat response is ready.
        self.right_panel.receive_message(response)
        self.conversation_history.append({"role": "assistant", "content": response})

    def on_asc_code_ready(self, asc_code):
        # Called when the .asc code is ready.
        if asc_code and asc_code != "N":
            self.left_panel.code_editor.setText(asc_code)
            self.conversation_history.append({"role": "assistant", "content": f"Generated ASC Code:\n{asc_code}"})
        else:
            self.left_panel.code_editor.setText("")
            self.conversation_history.append({"role": "assistant", "content": "No valid ASC code generated; query deemed irrelevant."})

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
