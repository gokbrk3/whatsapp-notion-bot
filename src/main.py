"""
Ana uygulama dosyası

WhatsApp-Notion bot'unun ana giriş noktası.
"""

import time
import sys
from datetime import datetime
from utils.config_loader import ConfigLoader
from utils.logger import get_logger
from core.message_parser import MessageParser
from core.notion_client import NotionClient
from core.whatsapp_listener import WhatsAppListener
from core.updater import Updater


def main():
    # Config ve logger yükle
    config = ConfigLoader()
    logger = get_logger()

    notion_client = NotionClient(config.get_notion_token(), config.get_parent_page_id())
    parser = MessageParser()
    updater = Updater(notion_client, parser, logger)
    listener = WhatsAppListener(config, logger)

    # Target date belirle
    target_date = config.get("target_date")
    if not target_date:
        target_date = datetime.now().strftime("%d.%m.%Y")
    
    # Başlangıç bilgilerini yazdır
    logger.info("=== WhatsApp → Notion Bot Başladı ===")
    logger.info(f"WhatsApp Grup: {config.get_whatsapp_group()}")
    logger.info(f"Headless: {config.get_headless()}")
    logger.info(f"Session Path: {config.get_session_path()}")
    logger.info(f"Hedef Tarih: {target_date}")

    # Login
    logger.info("WhatsApp'a giriş yapılıyor...")
    if not listener.login_to_whatsapp():
        logger.error("WhatsApp'a giriş yapılamadı.")
        sys.exit(1)
    logger.info("✅ WhatsApp'a giriş başarılı")

    # Grup aç
    logger.info(f"Grup açılıyor: {config.get_whatsapp_group()}")
    if not listener.open_group(config.get_whatsapp_group()):
        logger.warning("Grup açılamadı, tekrar dene!")
        # Basit retry
        for i in range(3):
            time.sleep(5)
            if listener.open_group(config.get_whatsapp_group()):
                break
        else:
            logger.error("Grup açılamadı, çıkılıyor.")
            sys.exit(1)
    logger.info("✅ Grup başarıyla açıldı")

    # Hedef tarih için database bul
    db_id = notion_client.get_database_by_date(target_date)
    if not db_id:
        logger.error(f"Hedef tarih için database bulunamadı: {target_date}")
        sys.exit(1)
    
    # Döngü
    try:
        while True:
            messages = listener.get_messages_by_date(target_date)
            for msg in messages:
                updater.process_text(msg, db_id)
            time.sleep(config.get_whatsapp_config().get("scan_interval", 5))
    except KeyboardInterrupt:
        logger.info("Bot kapatılıyor...")
        listener.driver.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
