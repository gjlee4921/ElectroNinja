import os
import logging

logger = logging.getLogger('electroninja')

def save_file(content, file_path):
    """
    Save content to a file, creating directories if needed.
    
    Args:
        content (str): Content to save
        file_path (str): Path to save to
        
    Returns:
        bool: True if successful
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write file
        with open(file_path, "w") as f:
            f.write(content)
            
        logger.info(f"File saved: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return False

def read_file(file_path):
    """
    Read content from a file.
    
    Args:
        file_path (str): Path to read from
        
    Returns:
        str: File content or empty string on error
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""
            
        with open(file_path, "r") as f:
            content = f.read()
            
        logger.info(f"File read: {file_path}")
        return content
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return ""