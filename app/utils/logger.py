import logging
import sys
import re
from app.config import settings

def filter_sensitive_data(message: str) -> str:
    """Mask tokens and sensitive authorization credentials in log messages."""
    if not isinstance(message, str):
        return str(message)
    # Mask WhatsApp Access Tokens or Bearer header tokens
    message = re.sub(r'Bearer\s+[A-Za-z0-9_\-\.\~]+', 'Bearer [REDACTED_TOKEN]', message)
    message = re.sub(r'access_token=[A-Za-z0-9_\-\.\~]+', 'access_token=[REDACTED_TOKEN]', message)
    if settings.WHATSAPP_ACCESS_TOKEN and len(settings.WHATSAPP_ACCESS_TOKEN) > 5:
        message = message.replace(settings.WHATSAPP_ACCESS_TOKEN, '[REDACTED_TOKEN]')
    if settings.ADMIN_API_KEY and len(settings.ADMIN_API_KEY) > 5:
        message = message.replace(settings.ADMIN_API_KEY, '[REDACTED_API_KEY]')
    return message

class SensitiveFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return filter_sensitive_data(formatted)

def setup_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = SensitiveFormatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

logger = setup_logger()
