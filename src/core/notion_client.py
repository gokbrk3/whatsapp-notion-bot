"""
Notion Client

Notion API ile etkileşim kuran sınıf.
"""

from typing import List, Optional
from notion_client import Client
from datetime import datetime, timedelta
import logging


class NotionClient:
    """
    Notion API ile etkileşim kuran sınıf.
    """
    
    def __init__(self, token: str, parent_page_id: str):
        """
        Notion Client'ı başlatır.
        
        Args:
            token: Notion API token
            parent_page_id: Ana sayfa ID'si
        """
        self.client = Client(auth=token)
        self.parent_page_id = parent_page_id
        self.logger = logging.getLogger("WhatsAppNotionBot")
        
    def get_today_and_yesterday_databases(self) -> List[str]:
        """
        Bugünün ve dünün tarihli sayfalarındaki database ID'lerini getirir.
        
        Returns:
            List[str]: Database ID'leri
        """
        # Parent page altındaki child blokları listele
        children = self.client.blocks.children.list(block_id=self.parent_page_id)
        
        # Bugün ve dünün tarihlerini hazırla
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        # Türkçe gün adları
        turkish_days = {
            'Monday': 'pazartesi',
            'Tuesday': 'salı', 
            'Wednesday': 'çarşamba',
            'Thursday': 'perşembe',
            'Friday': 'cuma',
            'Saturday': 'cumartesi',
            'Sunday': 'pazar'
        }
        
        # Tarih formatları oluştur
        date_formats = []
        for date in [today, yesterday]:
            # dd.mm.yyyy formatları
            date_formats.append(date.strftime("%d.%m.%Y"))
            date_formats.append(date.strftime("%d.%m.%Y") + " " + turkish_days[date.strftime("%A")])
            
            # dd-mm-yyyy formatları
            date_formats.append(date.strftime("%d-%m-%Y"))
            date_formats.append(date.strftime("%d-%m-%Y") + " - " + turkish_days[date.strftime("%A")])
            
            # dd/mm/yyyy formatları
            date_formats.append(date.strftime("%d/%m/%Y"))
            date_formats.append(date.strftime("%d/%m/%Y") + " " + turkish_days[date.strftime("%A")])
        
        # Tüm formatları küçük harfe çevir
        date_formats = [fmt.lower() for fmt in date_formats]
        
        database_ids = []
        
        for child in children.get('results', []):
            if child.get('type') == 'child_page':
                title = child.get('child_page', {}).get('title', '')
                # Başlığı normalize et (küçük harf, boşluk temizle)
                title_normalized = title.lower().strip()
                
                # Tarih formatlarından biriyle eşleşiyor mu kontrol et
                for date_format in date_formats:
                    if date_format in title_normalized:
                        # Sayfa içindeki database'leri bul
                        page_id = child['id']
                        page_children = self.client.blocks.children.list(block_id=page_id)
                        
                        for page_child in page_children.get('results', []):
                            if page_child.get('type') == 'child_database':
                                database_id = page_child['id']
                                database_ids.append(database_id)
                                self.logger.info(f"Tarih sayfası bulundu: {title} → DB: {database_id}")
                        break
        
        return database_ids
        
    def get_database_by_date(self, date_str: str) -> Optional[str]:
        """
        Belirli bir tarih için (gg.aa.yyyy) parent_page_id altındaki tabloyu bulur.
        1) Hem 27.09.2025, 27-09-2025, 27/09/2025 formatlarını hem de Türkçe gün adlarını kontrol eder.
        2) Sayfa veya database başlığında bu tarih geçen bloğu bulur.
        3) Eğer doğrudan database ise id'yi döndürür.
        4) Eğer sayfa ise içindeki ilk child_database id'sini döndürür.
        """
        import re
        d1 = date_str
        d2 = date_str.replace(".", "-")
        d3 = date_str.replace(".", "/")
        pat = re.compile(rf"({re.escape(d1)}|{re.escape(d2)}|{re.escape(d3)})", re.IGNORECASE)

        # Parent altında arama
        results = self.client.blocks.children.list(block_id=self.parent_page_id)
        for r in results.get("results", []):
            if r["type"] == "child_page":
                title = r["child_page"]["title"]
                if pat.search(title):
                    # Çocuk sayfanın içinde database ara
                    children = self.client.blocks.children.list(block_id=r["id"])
                    for ch in children.get("results", []):
                        if ch["type"] == "child_database":
                            return ch["id"]
            elif r["type"] == "child_database":
                title = r["child_database"]["title"]
                if pat.search(title):
                    return r["id"]
        return None
        
    def find_row_by_name(self, database_id: str, name: str) -> Optional[str]:
        """
        Database'de name ile eşleşen satırı bulur.
        
        Args:
            database_id: Database ID'si
            name: Aranacak isim
            
        Returns:
            Optional[str]: Bulunan satırın page_id'si
        """
        # Database'i query et
        results = self.client.databases.query(database_id=database_id)
        name_lower = name.lower()
        
        for row in results.get('results', []):
            properties = row.get('properties', {})
            
            # Title veya rich_text alanlarında name ara
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'title':
                    title_text = ''.join([text.get('plain_text', '') for text in prop_data.get('title', [])])
                    title_lower = title_text.lower()
                    # Tam eşleşme veya contains kontrolü
                    if name_lower == title_lower or name_lower in title_lower:
                        row_id = row['id']
                        self.logger.info(f"Eşleşen satır bulundu: {name} → {row_id}")
                        return row_id
                elif prop_data.get('type') == 'rich_text':
                    rich_text = ''.join([text.get('plain_text', '') for text in prop_data.get('rich_text', [])])
                    rich_lower = rich_text.lower()
                    # Tam eşleşme veya contains kontrolü
                    if name_lower == rich_lower or name_lower in rich_lower:
                        row_id = row['id']
                        self.logger.info(f"Eşleşen satır bulundu: {name} → {row_id}")
                        return row_id
        
        return None
        
    def update_status(self, database_id: str, row_id: str, status: str) -> bool:
        """
        Database satırının status alanını günceller.
        
        Args:
            database_id: Database ID'si
            row_id: Satır ID'si
            status: Yeni status
            
        Returns:
            bool: Güncelleme başarılı mı
        """
        try:
            # Database şemasını al
            database = self.client.databases.retrieve(database_id=database_id)
            properties = database.get('properties', {})
            
            # Status alanını bul
            status_field = None
            status_field_names = ['durum', 'status', 'state', 'gidildi', 'gidildi / gidilmedi']
            
            for field_name, field_data in properties.items():
                if field_name.lower() in status_field_names:
                    status_field = field_name
                    break
            
            if not status_field:
                return False
            
            field_data = properties[status_field]
            field_type = field_data.get('type')
            
            # Status mapping
            if status == "iptal":
                notion_value = "Gidilmedi"
            elif status == "kaldı":
                notion_value = "Kaldı"
            elif status == "gidildi":
                notion_value = "Gidildi"
            else:
                notion_value = status
            
            # Property type'a göre update yap
            if field_type == 'status':
                properties = {status_field: {"status": {"name": notion_value}}}
                self.logger.info(f"Update çağrısı: row={row_id}, kolon={status_field}, değer={notion_value}")
                self.client.pages.update(page_id=row_id, properties=properties)
                self.logger.info(f"Update başarılı: {notion_value}")
                return True
            elif field_type == 'select':
                update_data = {
                    status_field: {
                        'select': {'name': notion_value}
                    }
                }
                self.logger.info(f"Update çağrısı: row={row_id}, kolon={status_field}, değer={notion_value}")
                self.client.pages.update(page_id=row_id, properties=update_data)
                self.logger.info(f"Update başarılı: {notion_value}")
                return True
            elif field_type == 'multi_select':
                update_data = {
                    status_field: {
                        'multi_select': [{'name': notion_value}]
                    }
                }
                self.logger.info(f"Update çağrısı: row={row_id}, kolon={status_field}, değer={notion_value}")
                self.client.pages.update(page_id=row_id, properties=update_data)
                self.logger.info(f"Update başarılı: {notion_value}")
                return True
            elif field_type == 'rich_text':
                update_data = {
                    status_field: {
                        'rich_text': [{'text': {'content': notion_value}}]
                    }
                }
                self.logger.info(f"Update çağrısı: row={row_id}, kolon={status_field}, değer={notion_value}")
                self.client.pages.update(page_id=row_id, properties=update_data)
                self.logger.info(f"Update başarılı: {notion_value}")
                return True
            elif field_type == 'checkbox':
                checkbox_value = True if status == "gidildi" else False
                update_data = {
                    status_field: {
                        'checkbox': checkbox_value
                    }
                }
                self.logger.info(f"Update çağrısı: row={row_id}, kolon={status_field}, değer={checkbox_value}")
                self.client.pages.update(page_id=row_id, properties=update_data)
                self.logger.info(f"Update başarılı: {checkbox_value}")
                return True
            else:
                return False
            
        except Exception:
            return False
