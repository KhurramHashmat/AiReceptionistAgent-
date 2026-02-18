import logging
import os

def setup_logger(name):
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # File handler (detailed)
        file_handler = logging.FileHandler("logs/medconnect.log")
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        
        # Console handler (scannable)
        console_handler = logging.StreamHandler()
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_format)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger