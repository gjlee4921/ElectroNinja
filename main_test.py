import sys, os
import random
import string
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, Qt, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# Import custom modules (same as your main.py except we remove references to ChatManager)
from electroninja.gui.style import STYLE_SHEET, setup_fonts, COLORS
from electroninja.gui.top_bar import TopBar
from electroninja.gui.left_panel import LeftPanel
from electroninja.gui.middle_panel import MiddlePanel
from electroninja.gui.right_panel import RightPanel

# --------------------------------------------------------------------------------
# 1) Create a 'FakeChatManager' that returns random strings of length 100-300
# --------------------------------------------------------------------------------

class FakeChatManager:
    """Provides dummy methods to simulate LLM responses."""

    def get_random_string(self, length):
        """Generate a random ASCII string of a given length."""
        chars = string.ascii_letters + string.digits + " .,!?-"
        return "".join(random.choice(chars) for _ in range(length))

    def get_chat_response(self, user_input: str) -> str:
        """Return a random string (100-300 chars) simulating chat response."""
        length = random.randint(100, 300)
        return self.get_random_string(length)

    def get_asc_code(self, user_input: str) -> str:
        """Return a random string (100-300 chars) simulating .asc code."""
        length = random.randint(100, 300)
        return self.get_random_string(length)


# --------------------------------------------------------------------------------
# 2) Adapt the MainWindow class to use FakeChatManager instead of ChatManager
# --------------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ElectroNinja - Electrical Engineer Agent (Test Version)")
        self.setGeometry(100, 50, 1400, 800)  # Larger default size

        # Collapsed and expanded widths for the left panel
        self.left_panel_collapsed_width = 80
        self.left_panel_expanded_width = 0  # Calculated at runtime
        
        # Current circuit file and prompt
        self.current_circuit_file = None
        self.circuit_request_prompt = None  # Stores the latest circuit request
        
        # Conversation history: list of messages (each as a dict)
        self.conversation_history = []  # e.g., {"role": "user"/"assistant", "content": "..."}

        # Instead of the real ChatManager, use our FakeChatManager
        self.chat_manager = FakeChatManager()

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
            self.adjustPanelWidths()
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

        # For test version, we do NOT check keywords. Instead, we always produce random output:
        chat_response = self.chat_manager.get_chat_response(message)
        asc_code = self.chat_manager.get_asc_code(message)

        # Show the chat response in the right panel
        self.right_panel.receive_message(chat_response)
        self.conversation_history.append({"role": "assistant", "content": chat_response})

        # Show the random 'ASC code' in the left panel
        self.left_panel.code_editor.setText(asc_code)
        self.conversation_history.append({"role": "assistant", "content": f"Generated ASC Code:\n{asc_code}"})

    def compile_circuit(self):
        asc_code = self.left_panel.code_editor.toPlainText()
        if not asc_code.strip():
            self.right_panel.receive_message("Please enter some circuit code first!")
            return
        print("Compiling circuit code... (In test version, no real compilation.)")
        self.right_panel.receive_message("Circuit compiled successfully (Test version)!")
        self.middle_panel.circuit_display.setText("Circuit preview would be displayed here (Test version).")
        self.save_circuit()

    def save_circuit(self):
        if self.current_circuit_file is None:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_dir = f"output_{timestamp}"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            self.current_circuit_file = os.path.join(output_dir, "test_circuit.asc")
        with open(self.current_circuit_file, 'w') as f:
            f.write(self.left_panel.code_editor.toPlainText())
        self.right_panel.receive_message(f"Test circuit saved to {self.current_circuit_file}")
        self.conversation_history.append({"role": "system", "content": f"Test circuit saved to {self.current_circuit_file}"})

    def edit_with_ltspice(self):
        # In test version, we simply show a message instead of launching an external application
        if not self.current_circuit_file:
            self.save_circuit()
        print(f"[Test Version] Opening circuit in LTSpice: {self.current_circuit_file}")
        self.right_panel.receive_message("[Test Version] Pretending to open circuit in LTSpice...")
        self.conversation_history.append({"role": "system", "content": "[Test Version] Launched LTSpice with current circuit."})


def main():
    app = QApplication(sys.argv)
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
