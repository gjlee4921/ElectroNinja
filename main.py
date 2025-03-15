# main.py

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
import ctypes

# Try to fix COM initialization error
if sys.platform == 'win32':
    try:
        # Set single-threaded apartment mode for COM
        ctypes.OleDLL('ole32.dll').CoInitialize(None)
    except:
        pass

# Initialize configuration and logging
from electroninja.config.logging_config import setup_logging
from electroninja.config.settings import Config
from electroninja.ui.main_window import MainWindow

def main():
    """Main entry point for the application"""
    # Set up logging
    setup_logging()
    logger = logging.getLogger('electroninja')
    logger.info("ElectroNinja starting...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Set default font
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)
    
    # Initialize configuration and ensure directories exist
    config = Config()
    config.ensure_directories()
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Log application ready
    logger.info("ElectroNinja UI initialized and ready")
    
    # Start event loop
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())