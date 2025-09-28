"""
Logger

Logging yapılandırması ve yardımcı fonksiyonlar.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


def get_logger(name: str = "WhatsAppNotionBot") -> logging.Logger:
    """
    Singleton logger getirir veya oluşturur.
    
    Args:
        name: Logger adı
        
    Returns:
        logging.Logger: Yapılandırılmış logger
    """
    logger = logging.getLogger(name)
    
    # Logger zaten yapılandırılmışsa tekrar yapılandırma
    if logger.handlers:
        return logger
    
    # Log dizinini oluştur
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Logger seviyesini ayarla
    logger.setLevel(logging.INFO)
    
    # Formatter oluştur
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (RotatingFileHandler)
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "whatsapp_notion_bot.log"),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
