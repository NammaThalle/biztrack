import os
import shutil
from pathlib import Path
from src.utils.logger import logger

def cleanup_pycache(start_path: str = ".") -> None:
    """
    Recursively remove all __pycache__ directories and .pyc files from the project.
    This function should be called at the start of the application to ensure a clean state.
    
    Args:
        start_path: The root path to start searching from (default: current directory)
    """
    try:
        removed_dirs = 0
        removed_files = 0
        
        # Walk through all directories
        for root, dirs, files in os.walk(start_path):
            # Skip venv directory
            if 'venv' in root or '.git' in root:
                continue
                
            # Remove __pycache__ directories
            for dir_name in dirs[:]:  # Create a copy to modify during iteration
                if dir_name == '__pycache__':
                    cache_path = os.path.join(root, dir_name)
                    try:
                        shutil.rmtree(cache_path)
                        removed_dirs += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove {cache_path}: {e}")
                    dirs.remove(dir_name)  # Remove from dirs list to avoid processing
            
            # Remove .pyc files
            for file_name in files:
                if file_name.endswith('.pyc'):
                    file_path = os.path.join(root, file_name)
                    try:
                        os.remove(file_path)
                        removed_files += 1
                        logger.info(f"Removed .pyc file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {file_path}: {e}")
        
        if removed_dirs > 0 or removed_files > 0:
            logger.info(f"Cleanup complete: removed {removed_dirs} __pycache__ directories and {removed_files} .pyc files")
        else:
            logger.info("No cache files found to clean")
            
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def ensure_clean_state() -> None:
    """
    Ensure the application starts with a clean state by removing all cache files.
    This should be called at the very beginning of the application.
    """
    logger.info("Starting cleanup process...")
    cleanup_pycache()
    logger.info("Cleanup process completed") 