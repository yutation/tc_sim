"""
Utility functions for file operations.

This module provides helper functions for managing output files and directories.
"""

import os


def prepare_output_file(file_path: str) -> tuple[str, str, str]:
    """
    Prepare an output file path by creating necessary directories and cleaning up existing files.
    
    This function:
    1. Extracts the directory, filename (without extension), and extension from the given path
    2. Creates the directory if it doesn't exist
    3. Removes the file if it already exists
    
    Args:
        file_path: Full path to the output file
        
    Returns:
        A tuple containing:
        - directory: The directory path
        - file_name_without_extension: The base filename without extension
        - extension: The file extension (including the dot)
        
    Example:
        >>> prepare_output_file("/path/to/results/output.txt")
        ("/path/to/results", "output", ".txt")
    """
    # Extract directory and filename components
    directory = os.path.dirname(file_path)
    file_name_with_extension = os.path.basename(file_path)
    file_name_without_extension = os.path.splitext(file_name_with_extension)[0]
    extension = os.path.splitext(file_name_with_extension)[1]
    
    # Create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Remove existing file to ensure clean output
    if os.path.exists(file_path):
        os.remove(file_path)
    
    return directory, file_name_without_extension, extension
