# Atlas Library

SQLite tabanli, Streamlit ile hazirlanmis ev tipi okuma takip uygulamasi.

## Ozellikler

- Kitap ekleme, katalogda arama ve gruba gore filtreleme
- Cocuklar icin uygun, anlasilir kitap gruplari
- Okunmamis kitaplara oncelik veren iki kitap onerisi
- Okunma sayisi, son okuma tarihi ve okuma karnesi
- Okuma kaydini sifirlama ve kitap silme
- Verilerin yerel SQLite veritabaninda kalici saklanmasi

## Kurulum

```bash
cd /Users/anilates/Library/CloudStorage/OneDrive-Personal/Documents/Atlas/Books/Atlas_Library
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run Library.py
```

Veritabani ilk calistirmada `data/atlas_library.db` yolunda otomatik olusturulur.
# ATLAS_LIBRARY
