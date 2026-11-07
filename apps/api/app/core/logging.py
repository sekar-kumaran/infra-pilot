import logging
import sys
from asgi_correlation_id import correlation_id
from pythonjsonlogger import jsonlogger
from app.core.config import settings

class SafeJsonFormatter(jsonlogger.JsonFormatter):
    def _perform_rename_log_fields(self, log_record):
        for old_field_name, new_field_name in self.rename_fields.items():
            if old_field_name in log_record:
                log_record[new_field_name] = log_record.pop(old_field_name)

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = correlation_id.get()
        record.environment = settings.APP_ENV
        record.service = settings.APP_NAME
        return True

def setup_logging():
    logger = logging.getLogger()
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = SafeJsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(environment)s %(service)s',
        rename_fields={"levelname": "level", "asctime": "timestamp"}
    )
    
    logHandler.setFormatter(formatter)
    logHandler.addFilter(CorrelationIdFilter())
    logger.addHandler(logHandler)
    
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    return logger
