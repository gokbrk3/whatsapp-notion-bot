"""
Message Parser

WhatsApp mesajlarını parse ederek Notion için uygun formata çeviren sınıf.
"""

from typing import Dict


class MessageParser:
    """
    WhatsApp mesajlarını parse eden sınıf.
    """
    
    def parse_message(self, text: str) -> Dict:
        """
        Mesajı parse eder ve status belirler.
        
        Args:
            text: Ham mesaj metni
            
        Returns:
            Dict: Parse edilmiş mesaj verisi
        """
        text_lower = text.lower()
        
        # Status belirleme
        if "iptal" in text_lower:
            status = "iptal"
        elif "ertelendi" in text_lower or "kaldı" in text_lower or "kaldi" in text_lower:
            status = "kaldı"
        elif "gidildi" in text_lower:
            status = "gidildi"
        else:
            status = None
        
        # Name: orijinal metinden anahtar kelimeler çıkarılmış hali
        name = text
        for keyword in ["iptal", "ertelendi", "kaldı", "kaldi", "gidildi"]:
            name = name.replace(keyword, "").replace(keyword.capitalize(), "").replace(keyword.upper(), "")
        
        name = name.strip()
        
        return {"name": name, "status": status}
