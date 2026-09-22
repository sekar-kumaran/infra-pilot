import logging
import sys
from asgi_correlation_id import correlation_id
from pythonjsonlogger import jsonlogger
from app.core.config import settings

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = correlation_id.get()
        record.environment = settings.APP_ENV
        record.service = settings.APP_NAME
        return True

def setup_logging():
    logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(environment)s %(service)s', rename_fields={"levelname": "level", "asctime": "timestamp"})
    
    logHandler.setFormatter(formatter)
    logHandler.addFilter(CorrelationIdFilter())
    logger.addHandler(logHandler)
    
    # Set levels for third-party libraries to avoid noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return logger
