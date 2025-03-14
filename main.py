#!/usr/bin/env python3
"""
ElectroNinja - AI Electrical Engineer

An AI-powered application that helps design electronic circuits
using LTSpice and AI models for feedback and refinement.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

# Initialize configuration and logging
from electroninja.config import logger
from electroninja.ui.main_window import MainWindow

def main():
    """Main entry point for the application"""
    # Log application startup
    logger.info("ElectroNinja starting...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Set default font
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Log application ready
    logger.info("ElectroNinja UI initialized and ready")
    
    # Start event loop
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())