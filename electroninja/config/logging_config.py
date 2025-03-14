# logging_config.py


import logging
import os
from datetime import datetime

def setup_logging():
    """Configure logging for the application"""
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate log file name with timestamp
    log_file = os.path.join(logs_dir, f"electroninja_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Create a logger
    logger = logging.getLogger('electroninja')
    logger.info("Logging initialized")
    
    return logger