import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, Qt, pyqtSlot
from PyQt5.QtGui import QFont

# Import your custom modules
from style import STYLE_SHEET, setup_fonts, COLORS
from top_bar import TopBar
from left_panel import LeftPanel
from middle_panel import MiddlePanel
from right_panel import RightPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ElectroNinja - Electrical Engineer Agent")
        self.setGeometry(100, 50, 1400, 800)  # Larger default size

        # Collapsed and expanded widths for the left panel
        self.left_panel_collapsed_width = 80
        self.left_panel_expanded_width = 0  # calculated at runtime

        self.initUI()
        self.connectSignals()
        self.adjustPanelWidths()

    def initUI(self):
        # Optional custom fonts
        if 'setup_fonts' in globals():
            setup_fonts(QApplication.instance())

        self.setStyleSheet(STYLE_SHEET)

        # Central widget & main vertical layout
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
        self.left_panel.setSizePolicy(QWidget().sizePolicy())  # We'll animate min/max
        self.middle_panel.setSizePolicy(QWidget().sizePolicy())  # Expanding center
        self.right_panel.setSizePolicy(QWidget().sizePolicy())  # We'll fix its width

        # Initially, set the left panel min/max so it starts "expanded"
        self.left_panel.setMinimumWidth(self.left_panel_collapsed_width)
        self.left_panel.setMaximumWidth(300)  # Temporary, replaced in adjustPanelWidths()

        # Add them in left->middle->right order
        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.middle_panel)
        self.main_layout.addWidget(self.right_panel)

        # Connect the toggle signal
        self.left_panel.toggleRequested.connect(self.on_left_panel_toggle)

    def connectSignals(self):
        """Connect all signals and slots."""
        self.right_panel.messageSent.connect(self.handle_message)
        self.left_panel.compile_button.clicked.connect(self.compile_circuit)
        self.middle_panel.edit_button.clicked.connect(self.edit_with_ltspice)

    def on_left_panel_toggle(self, is_expanding):
        """Handle the toggle button to expand/collapse the left panel."""
        if is_expanding:
            # Expand from current maxWidth to expanded width
            current_width = self.left_panel.maximumWidth()
            self.adjustPanelWidths()  # Recalculate expanded width
            self.left_panel.showCodeEditor()
            self.animate_left_panel(current_width, self.left_panel_expanded_width)
        else:
            # Collapse from current maxWidth to collapsed width
            current_width = self.left_panel.maximumWidth()
            self.animate_left_panel(current_width, self.left_panel_collapsed_width)
            self.left_panel.hideCodeEditor()

    def animate_left_panel(self, start_width, end_width):
        """Animate the maximumWidth property of the left panel."""
        animation = QPropertyAnimation(self.left_panel, b"maximumWidth")
        animation.setDuration(600)  # 600 ms for a smooth animation
        animation.setStartValue(start_width)
        animation.setEndValue(end_width)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        def finalize():
            self.left_panel.setMaximumWidth(end_width)

        animation.finished.connect(finalize)
        animation.start()
        self.current_animation = animation  # Prevent GC

    def adjustPanelWidths(self):
        """
        Make the left panel and the right panel the same or custom widths,
        with the middle panel expanding in between.
        """
        total_width = self.width() - 40  # 40 px for margins & spacing
        
        # Example: left=22%, middle=50%, right=28%
        left_width = int(total_width * 0.22)
        right_width = int(total_width * 0.28)

        self.left_panel_expanded_width = left_width

        # If left panel is open, set its max to left_width; else collapsed
        if self.left_panel.toggle_button.isChecked():
            self.left_panel.setMaximumWidth(left_width)
        else:
            self.left_panel.setMaximumWidth(self.left_panel_collapsed_width)

        # Right panel is fixed at right_width
        self.right_panel.setFixedWidth(right_width)

    def resizeEvent(self, event):
        """Maintain proportions on window resize."""
        super().resizeEvent(event)
        self.adjustPanelWidths()

    @pyqtSlot(str)
    def handle_message(self, message):
        """Handle messages from the chat panel."""
        print(f"Received message: {message}")
        response = self.generate_dummy_response(message)
        self.right_panel.receive_message(response)

    def generate_dummy_response(self, message):
        """Generate a dummy response for demonstration."""
        text = message.lower()
        if "hello" in text or "hi" in text:
            return "Hello! I'm ElectroNinja. How can I help with your circuit design?"
        elif "circuit" in text:
            return "I can help you design and analyze circuits. What kind of circuit are you trying to build?"
        elif "ltspice" in text:
            return "LTspice is a powerful circuit simulation tool. You can use the editor button to open your design in LTSpice when you're ready."
        elif "help" in text:
            return "I can help you design circuits, analyze components, or explain electrical concepts. Please describe what you're trying to build!"
        elif any(word in text for word in ["resistor", "capacitor", "inductor", "transistor", "diode"]):
            return "I see you're asking about a specific component. Could you provide more details about your design?"
        else:
            return "I'll analyze your request and help design the appropriate circuit. Could you provide more details about your requirements?"

    def compile_circuit(self):
        """Compile the .asc code and update the circuit display."""
        asc_code = self.left_panel.code_editor.toPlainText()
        print("Compiling circuit code...")
        self.right_panel.receive_message("Circuit compiled successfully! You can see the result in the middle panel.")
        self.middle_panel.circuit_display.setText("Circuit automatically generated and displayed here")

    def edit_with_ltspice(self):
        """Open the current circuit in LTSpice."""
        print("Opening circuit in LT Spice...")
        self.right_panel.receive_message("Opening circuit in LTSpice. This would launch the external application in a real implementation.")

def main():
    app = QApplication(sys.argv)
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
