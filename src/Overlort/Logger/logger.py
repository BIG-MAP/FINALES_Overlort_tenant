from pydantic import BaseModel
from typing import Dict

class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = "Overlogger"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(funcName)s | %(message)s"
    LOG_LEVEL: str = "DEBUG"

    # Logging config
    version: int = 1
    disable_existing_loggers: bool = True
    formatters: Dict = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S CET",
        },
    }
    handlers: Dict = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers: Dict = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }
    
