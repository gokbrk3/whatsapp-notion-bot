"""
Config Loader

Konfigürasyon dosyalarını yükleyen sınıf.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """
    Konfigürasyon dosyalarını yükleyen sınıf.
    """
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Config Loader'ı başlatır.
        
        Args:
            config_path: Konfigürasyon dosya yolu
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
        
    def _load_config(self) -> None:
        """
        Konfigürasyon dosyasını yükler.
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            raise ValueError(f"Konfigürasyon dosyası bulunamadı: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Konfigürasyon dosyası geçersiz JSON: {e}")
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Konfigürasyon değerini getirir.
        
        Args:
            key: Konfigürasyon anahtarı
            default: Varsayılan değer
            
        Returns:
            Any: Konfigürasyon değeri
        """
        return self.config.get(key, default)
        
    def get_notion_token(self) -> str:
        """
        Notion token'ını getirir.
        
        Returns:
            str: Notion token
            
        Raises:
            ValueError: Token boş veya geçersizse
        """
        token = self.get("notion_token")
        if not token or token == "secret_xxx":
            raise ValueError("Notion token boş veya geçersiz")
        return token
        
    def get_parent_page_id(self) -> str:
        """
        Parent page ID'sini getirir ve normalize eder.
        
        Returns:
            str: Normalize edilmiş page ID
            
        Raises:
            ValueError: Page ID boş veya geçersizse
        """
        page_id = self.get("parent_page_id")
        if not page_id or page_id == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee":
            raise ValueError("Parent page ID boş veya geçersiz")
        
        # ? işaretinden sonrasını at
        if "?" in page_id:
            page_id = page_id.split("?")[0]
            
        return page_id
        
    def get_whatsapp_group(self) -> str:
        """
        WhatsApp grup adını getirir.
        
        Returns:
            str: WhatsApp grup adı
            
        Raises:
            ValueError: Grup adı boşsa
        """
        group = self.get("whatsapp_group")
        if not group:
            raise ValueError("WhatsApp grup adı boş")
        return group
        
    def get_headless(self) -> bool:
        """
        Headless mod ayarını getirir.
        
        Returns:
            bool: Headless mod aktif mi
        """
        return self.get("headless", False)
        
    def get_session_path(self) -> str:
        """
        Session path'ini getirir ve klasörü oluşturur.
        
        Returns:
            str: Mutlak session path
            
        Raises:
            ValueError: Session path boşsa
        """
        session_path = self.get("session_path")
        if not session_path:
            raise ValueError("Session path boş")
            
        # Windows mutlak yol olsun
        if not os.path.isabs(session_path):
            session_path = os.path.abspath(session_path)
            
        # Klasör yoksa oluştur
        os.makedirs(session_path, exist_ok=True)
        
        return session_path
        
    def get_selenium_config(self) -> Dict[str, Any]:
        """
        Selenium konfigürasyonunu getirir.
        
        Returns:
            Dict[str, Any]: Selenium ayarları
        """
        selenium_config = self.get("selenium", {})
        return {
            "implicit_wait": selenium_config.get("implicit_wait", 10),
            "window_size": selenium_config.get("window_size", [1200, 800])
        }
        
    def get_whatsapp_config(self) -> Dict[str, Any]:
        """
        WhatsApp konfigürasyonunu getirir.
        
        Returns:
            Dict[str, Any]: WhatsApp ayarları
        """
        whatsapp_config = self.get("whatsapp", {})
        return {
            "scan_interval": whatsapp_config.get("scan_interval", 5)
        }
