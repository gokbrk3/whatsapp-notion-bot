"""
Config GUI

Konfigürasyon ayarları için GUI arayüzü.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import subprocess

CONFIG_PATH = os.path.join("config", "config.json")

class ConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp → Notion Bot Ayarları")

        # Alanlar
        self.fields = {
            "notion_token": tk.StringVar(),
            "parent_page_id": tk.StringVar(),
            "whatsapp_group": tk.StringVar(),
            "headless": tk.BooleanVar(),
            "session_path": tk.StringVar(),
            "target_date": tk.StringVar()
        }

        # Arayüz
        tk.Label(root, text="Notion Token").grid(row=0, column=0, sticky="w")
        tk.Entry(root, textvariable=self.fields["notion_token"], width=50).grid(row=0, column=1)

        tk.Label(root, text="Parent Page ID").grid(row=1, column=0, sticky="w")
        tk.Entry(root, textvariable=self.fields["parent_page_id"], width=50).grid(row=1, column=1)

        tk.Label(root, text="WhatsApp Grup Adı").grid(row=2, column=0, sticky="w")
        tk.Entry(root, textvariable=self.fields["whatsapp_group"], width=50).grid(row=2, column=1)

        tk.Checkbutton(root, text="Headless (Arka planda çalıştır)", variable=self.fields["headless"]).grid(row=3, column=1, sticky="w")

        tk.Label(root, text="Session Path").grid(row=4, column=0, sticky="w")
        tk.Entry(root, textvariable=self.fields["session_path"], width=50).grid(row=4, column=1)
        tk.Button(root, text="Gözat", command=self.browse_session).grid(row=4, column=2)

        tk.Label(root, text="Hedef Tarih (gg.aa.yyyy)").grid(row=5, column=0, sticky="w")
        tk.Entry(root, textvariable=self.fields["target_date"], width=50).grid(row=5, column=1)

        # Butonlar
        tk.Button(root, text="Kaydet", command=self.save_config).grid(row=6, column=0, pady=10)
        tk.Button(root, text="Kaydet + Botu Başlat", command=self.save_and_start).grid(row=6, column=1, pady=10)

        # Var olan config'i yükle
        self.load_config()

    def browse_session(self):
        path = filedialog.askdirectory()
        if path:
            self.fields["session_path"].set(path)

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.fields["notion_token"].set(data.get("notion_token", ""))
                self.fields["parent_page_id"].set(data.get("parent_page_id", "").split("?")[0])
                self.fields["whatsapp_group"].set(data.get("whatsapp_group", ""))
                self.fields["headless"].set(data.get("headless", False))
                self.fields["session_path"].set(data.get("session_path", ""))
                self.fields["target_date"].set(data.get("target_date", ""))

    def save_config(self):
        data = {k: v.get() if not isinstance(v, tk.BooleanVar) else v.get() for k, v in self.fields.items()}
        # parent_page_id normalize et
        if "?" in data["parent_page_id"]:
            data["parent_page_id"] = data["parent_page_id"].split("?")[0]

        # Varsayılan config ekleri
        data.update({
            "silent_mode": False,
            "whatsapp": {"scan_interval": 5},
            "selenium": {"implicit_wait": 10, "window_size": [1200, 800]}
        })

        os.makedirs("config", exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("Kaydedildi", "Ayarlar başarıyla kaydedildi.")

    def save_and_start(self):
        self.save_config()
        subprocess.Popen(["python", "src/main.py"])

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()
