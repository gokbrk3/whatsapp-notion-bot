# WhatsApp-Notion Bot

WhatsApp mesajlarını dinleyip Notion'a aktaran otomatik bot sistemi.

## Amaç

Bu bot, belirtilen WhatsApp grubundaki mesajları dinleyerek bunları Notion sayfalarına otomatik olarak aktarır. Özellikle grup sohbetlerini Notion'da arşivlemek için tasarlanmıştır.

## Hızlı Başlangıç

### Gereksinimler

- Python 3.8+
- Chrome/Chromium tarayıcı
- Notion hesabı ve API token

### Kurulum

1. Projeyi klonlayın:
```bash
git clone <repository-url>
cd whatsapp-notion-bot
```

2. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

3. Konfigürasyonu ayarlayın:
```bash
# config/config.json dosyasını düzenleyin
```

### Konfigürasyon

`config/config.json` dosyasında aşağıdaki alanları ayarlayın:

- `notion_token`: Notion API token'ınız
- `parent_page_id`: Mesajların ekleneceği Notion sayfa ID'si
- `whatsapp_group`: Dinlenecek WhatsApp grup adı
- `headless`: Tarayıcıyı gizli modda çalıştır (true/false)
- `session_path`: WhatsApp oturum dosyası yolu

### Çalıştırma

```bash
# Ana uygulamayı başlat
python src/main.py

# GUI ile konfigürasyon
python src/gui/config_gui.py
```

## Özellikler

- WhatsApp Web entegrasyonu
- Notion API entegrasyonu
- Otomatik mesaj parsing
- GUI konfigürasyon arayüzü
- Log sistemi
- Güncelleme kontrolü

## Geliştirme

Testleri çalıştırmak için:
```bash
python -m pytest tests/
```

## Lisans

MIT License
