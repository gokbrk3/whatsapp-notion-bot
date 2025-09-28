"""
Test Parser Run

Message parser için test sınıfı.
"""

from core.message_parser import MessageParser

def run_tests():
    parser = MessageParser()
    samples = [
        "Songül iptal",
        "Yüksel Can ertelendi",
        "Aynur kaldı",
        "Mehmet gidildi",
        "Selma merhaba"
    ]

    for text in samples:
        result = parser.parse_message(text)
        print(f"Girdi: {text} → Çıktı: {result}")

if __name__ == "__main__":
    run_tests()
