import logging
import sys
from pathlib import Path

def setup_logging(name="antigravity"):
    """
    Sets up a colored logger for the application.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Also log to file
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "antigravity.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
