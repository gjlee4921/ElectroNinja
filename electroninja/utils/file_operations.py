#file_operations.py

import os
import shutil
import tempfile
import logging
from electroninja.utils.error_handler import FileError

logger = logging.getLogger('electroninja')

def create_temp_file(content, suffix=".asc", prefix="electroninja_", dir=None):
    """
    Create a temporary file with the given content
    
    Args:
        content (str): Content to write to the file
        suffix (str): File suffix
        prefix (str): File prefix
        dir (str): Directory to create the file in
        
    Returns:
        str: Path to the created temporary file
    """
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=suffix, 
            prefix=prefix, 
            mode="w", 
            dir=dir
        )
        
        # Write content to the file
        temp_file.write(content)
        temp_file_path = temp_file.name
        temp_file.close()
        
        logger.info(f"Created temporary file: {temp_file_path}")
        return temp_file_path
        
    except Exception as e:
        raise FileError(f"Failed to create temporary file: {str(e)}")

def save_file(content, file_path, encoding="utf-8"):
    """
    Save content to a file
    
    Args:
        content (str): Content to write to the file
        file_path (str): Path to the file
        encoding (str): File encoding
        
    Returns:
        str: Path to the saved file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write content to the file
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
            
        logger.info(f"Saved file: {file_path}")
        return file_path
        
    except Exception as e:
        raise FileError(f"Failed to save file: {str(e)}")

def read_file(file_path, encoding="utf-8", errors="replace"):
    """
    Read content from a file
    
    Args:
        file_path (str): Path to the file
        encoding (str): File encoding
        errors (str): How to handle encoding errors
        
    Returns:
        str: Content of the file
    """
    try:
        if not os.path.exists(file_path):
            raise FileError(f"File not found: {file_path}")
            
        with open(file_path, "r", encoding=encoding, errors=errors) as f:
            content = f.read()
            
        return content
        
    except Exception as e:
        if isinstance(e, FileError):
            raise e
        raise FileError(f"Failed to read file: {str(e)}")

def copy_file(src, dst):
    """
    Copy a file from source to destination
    
    Args:
        src (str): Source file path
        dst (str): Destination file path
        
    Returns:
        str: Path to the destination file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        
        # Copy the file
        shutil.copy2(src, dst)
        
        logger.info(f"Copied file from {src} to {dst}")
        return dst
        
    except Exception as e:
        raise FileError(f"Failed to copy file: {str(e)}")

def create_output_directory(base_dir):
    """
    Create a new output directory with incremental naming
    
    Args:
        base_dir (str): Base directory
        
    Returns:
        str: Path to the created directory
    """
    try:
        # Create base directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        
        # Find the next available directory name
        iteration = 0
        while os.path.exists(os.path.join(base_dir, f"output-{iteration}")):
            iteration += 1
            
        # Create the new directory
        output_dir = os.path.join(base_dir, f"output-{iteration}")
        os.makedirs(output_dir)
        
        logger.info(f"Created output directory: {output_dir}")
        return output_dir
        
    except Exception as e:
        raise FileError(f"Failed to create output directory: {str(e)}")