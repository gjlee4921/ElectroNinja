"""Custom signals for ElectroNinja application"""
from PyQt5.QtCore import QObject, pyqtSignal

class CircuitSignals(QObject):
    """Signals related to circuit processing"""
    
    # Signal emitted when a circuit processing begins
    processingStarted = pyqtSignal(str)  # Message
    
    # Signal emitted when a circuit processing completes
    processingComplete = pyqtSignal(bool, str, str)  # Success, asc_path, image_path
    
    # Signal emitted for status updates during processing
    statusUpdate = pyqtSignal(str)  # Status message
    
    # Signal emitted when an error occurs
    errorOccurred = pyqtSignal(str)  # Error message

class ChatSignals(QObject):
    """Signals related to chat interactions"""
    
    # Signal emitted when a message is sent by the user
    messageSent = pyqtSignal(str)  # Message text
    
    # Signal emitted when a response is received
    responseReceived = pyqtSignal(str)  # Response text