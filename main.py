# main.py

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
import ctypes

# Try to fix COM initialization error on Windows
if sys.platform == 'win32':
    try:
        ctypes.OleDLL('ole32.dll').CoInitialize(None)
    except:
        pass

from electroninja.config.logging_config import setup_logging
from electroninja.config.settings import Config
from electroninja.ui.main_window import MainWindow

# 1) Import your styling utilities
from electroninja.ui.styles import STYLE_SHEET, setup_fonts


def main():
    """Main entry point for the application"""
    # Set up logging
    setup_logging()
    logger = logging.getLogger('electroninja')
    logger.info("ElectroNinja starting...")

    # Create Qt application
    app = QApplication(sys.argv)
    
    # 2) Setup any custom fonts you might have
    setup_fonts(app)

    # 3) Apply the dark theme stylesheet
    app.setStyleSheet(STYLE_SHEET)

    # Set default font (optional)
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)
    
    # Initialize configuration
    config = Config()
    config.ensure_directories()

    # Create and show main window
    window = MainWindow()
    window.show()
    
    logger.info("ElectroNinja UI initialized and ready")
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
