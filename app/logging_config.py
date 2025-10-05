import logging
import os
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Handle structured logging data
        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)
        
        # Handle when dict is passed directly to logger methods
        if isinstance(record.msg, dict):
            log_record.update(record.msg)
            log_record["message"] = ""  # Clear redundant message
        
        # Return JSON without extra newline (handler will add it)
        return json.dumps(log_record)

def setup_logging():
    log_dir = '/app/logs/'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'api.log')

    logger = logging.getLogger('sanrio_api')
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Use line buffering and explicit terminator
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.terminator = '\n'  # Ensure newline termination
    formatter = JsonFormatter()
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.propagate = False
    
    return logger
