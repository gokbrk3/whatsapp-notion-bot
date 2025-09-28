"""
Updater

Notion veritabanlarını güncelleyen sınıf.
"""

from typing import Dict, List


class Updater:
    """
    Notion veritabanlarını güncelleyen sınıf.
    """
    
    def __init__(self, notion_client, parser, logger):
        """
        Updater'ı başlatır.
        
        Args:
            notion_client: NotionClient instance
            parser: MessageParser instance
            logger: Logger instance
        """
        self.notion_client = notion_client
        self.parser = parser
        self.logger = logger
        
    def process_text(self, text: str) -> None:
        """
        Metni işler ve Notion'da günceller.
        
        Args:
            text: İşlenecek metin
        """
        # Parser ile mesajı parse et
        data = self.parser.parse_message(text)
        
        # Status None ise uyarı ver ve çık
        if data["status"] is None:
            self.logger.warning(f"Durum bulunamadı: {text}")
            return
        
        # Bugünün ve dünün database'lerini al
        databases = self.notion_client.get_today_and_yesterday_databases()
        
        # Her database için kontrol et
        for db in databases:
            row_id = self.notion_client.find_row_by_name(db, data["name"])
            
            if row_id:
                # Status güncelle
                ok = self.notion_client.update_status(db, row_id, data["status"])
                
                if ok:
                    self.logger.info(f"Güncellendi: {data}")
                else:
                    self.logger.error(f"Güncellenemedi: {data}")
                return
        
        # Hiç eşleşme bulunamadı
        self.logger.warning(f"Kayıt bulunamadı: {data}")
