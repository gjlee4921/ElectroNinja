import logging
import traceback
from PyQt5.QtWidgets import QMessageBox

logger = logging.getLogger('electroninja')

class ModelError(Exception):
    """Error from the LLM model"""
    pass

class LTSpiceError(Exception):
    """Error from LTSpice operations"""
    pass

def handle_error(error, parent=None, title="Error"):
    """
    Handle an error by logging it and optionally showing a message box.
    
    Args:
        error (Exception): The error to handle
        parent (QWidget, optional): Parent widget for message box
        title (str, optional): Title for message box
        
    Returns:
        str: Error message
    """
    error_msg = str(error)
    logger.error(f"{title}: {error_msg}")
    logger.error(traceback.format_exc())
    
    if parent:
        QMessageBox.critical(parent, title, error_msg)
        
    return error_msg