"""Logging configuration"""

import logging
from src.config import get_config

config = get_config()

def get_logger(name):
    """Get configured logger"""
    logger = logging.getLogger(name)
    logger.setLevel(config.LOG_LEVEL)
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
