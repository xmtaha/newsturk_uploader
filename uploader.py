import requests
import os
import time

API_URL = "https://usenetturk.cc/api/upload"

KATEGORILER = {
    15: "E-Kitap", 
    9: "Film", 
    4: "Yerli Diziler", 
    1: "Yerli Filmler", 
    10: "Dizi", 
    5: "Yabancı Diziler TR (Dublaj)", 
    2: "Yabancı Filmler TR (Dublaj)", 
    12: "Yabancı Müzik", 
    17: "Lossless Müzik", 
    11: "Ses Dosyası", 
    6: "Yabancı Diziler ORJ (Altyazılı/Orijinal)", 
    3: "Yabancı Filmler ORJ (Altyazılı/Orijinal)", 
    8: "Yerli Müzik", 
    18: "MP3", 
    19: "Spor", 
    13: "Türkçe Ses", 
    14: "Kitap", 
    16: "Kurslar", 
    7: "Programlar"
}

class Uploader:
    def __init__(self, api_key, logger=None):
        self.api_key = api_key
        self.logger = logger

    def log(self, message):
        if self.logger:
            self.logger(message)
        else:
            print(message)

    def upload_files(self, file_paths, category_id, progress_callback=None):
        total = len(file_paths)
        basarili = 0
        basarisiz = 0
        
        for i, file_path in enumerate(file_paths):
            if not file_path.lower().endswith('.nzb'):
                self.log(f"⚠️ Atlandı (NZB değil): {os.path.basename(file_path)}")
                continue

            filename = os.path.basename(file_path)
            self.log(f"📤 Yükleniyor [{i+1}/{total}]: {filename}")
            
            try:
                with open(file_path, 'rb') as f:
                    files = {
                        'file': (filename, f, 'application/x-nzb')
                    }
                    data = {
                        'apikey': self.api_key,
                        'category_id': category_id,
                        'cat': category_id
                    }

                    # POST isteği
                    response = requests.post(API_URL, files=files, data=data, timeout=60)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            tmdb_status = '✅ Eşleşti' if result['nzb'].get('tmdb_matched') else '❌ Eşleşmedi'
                            self.log(f"   ✅ BAŞARILI! ID: {result['nzb']['id']} | TMDB: {tmdb_status}")
                            basarili += 1
                        else:
                            self.log(f"   ⚠️  Sunucu Hatası: {result.get('message', 'Bilinmeyen hata')}")
                            basarisiz += 1
                    else:
                        self.log(f"   ❌ HTTP Hata {response.status_code}: {response.text[:100]}")
                        basarisiz += 1

            except Exception as e:
                self.log(f"   ❌ Kritik Hata: {str(e)}")
                basarisiz += 1
            
            if progress_callback:
                progress_callback(int((i + 1) / total * 100))
        
        self.log("="*30)
        self.log(f"🏁 İŞLEM TAMAMLANDI")
        self.log(f"✅ Başarılı: {basarili}")
        self.log(f"❌ Başarısız: {basarisiz}")

