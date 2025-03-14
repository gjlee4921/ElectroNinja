# error_handler.py

import logging
import traceback
from PyQt5.QtWidgets import QMessageBox

# Custom exceptions
class ElectroNinjaError(Exception):
    """Base exception for all ElectroNinja errors"""
    pass

class LTSpiceError(ElectroNinjaError):
    """Exception raised for errors in LTSpice processing"""
    pass

class ModelError(ElectroNinjaError):
    """Exception raised for errors in LLM model interactions"""
    pass

class FileError(ElectroNinjaError):
    """Exception raised for errors in file operations"""
    pass

def log_error(error, context=None):
    """Log an error with stack trace and context info"""
    logger = logging.getLogger('electroninja')
    error_message = f"{type(error).__name__}: {str(error)}"
    
    if context:
        error_message = f"{error_message} - Context: {context}"
    
    logger.error(error_message)
    logger.error(traceback.format_exc())
    
    return error_message

def show_error_dialog(parent, title, message, details=None):
    """Show an error dialog to the user"""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if details:
        msg_box.setDetailedText(details)
    
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()

def handle_error(error, parent=None, context=None, show_dialog=True):
    """Comprehensive error handling function"""
    # Log the error
    error_message = log_error(error, context)
    
    # Show dialog if requested and parent widget is provided
    if show_dialog and parent:
        show_error_dialog(
            parent, 
            "Error", 
            f"An error occurred: {str(error)}", 
            traceback.format_exc()
        )
    
    return error_message