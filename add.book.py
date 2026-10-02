import sqlite3
import requests
import os

# Veritabanı yolunu projene göre otomatik ayarlar
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "atlas_library.db") # veya dosya yolun neyse

def fetch_book_from_google(book_title):
    """Google Books API kullanarak kitap bilgilerini internetten çeker"""
    url = f"https://www.googleapis.com/books/v1/volumes?q={requests.utils.quote(book_title)}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                volume_info = data["items"][0]["volumeInfo"]
                
                title = volume_info.get("title", book_title)
                authors = ", ".join(volume_info.get("authors", ["Bilinmiyor"]))
                page_count = volume_info.get("pageCount", 32) # Bulamazsa çocuk kitapları için standart 32
                if not page_count:
                    page_count = 32
                
                thumbnail = volume_info.get("imageLinks", {}).get("thumbnail", "")
                
                return {
                    "title": title,
                    "author": authors,
                    "pages": page_count,
                    "cover_url": thumbnail
                }
    except Exception as e:
        print(f"API Hatası: {e}")
    
    # API bulamazsa varsayılan değerler döndürür
    return {
        "title": book_title,
        "author": "Bilinmiyor",
        "pages": 32,
        "cover_url": ""
    }

def add_book_to_db(book_title):
    book_info = fetch_book_from_google(book_title)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tablo yapına göre (tablo adını kendi veritabanına göre güncelleyebilirsin)
    # Örnek tablo: books (title, author, pages, cover_url, status)
    try:
        cursor.execute("""
            INSERT INTO books (title, author, pages, cover_url, status)
            VALUES (?, ?, ?, ?, ?)
        """, (book_info["title"], book_info["author"], book_info["pages"], book_info["cover_url"], "Okunmadı"))
        
        conn.commit()
        print(f"Başarıyla eklendi: {book_info['title']} ({book_info['author']} - {book_info['pages']} sayfa)")
    except sqlite3.OperationalError as e:
        print(f"Tablo adı veya sütun hatası (Tablo adını kontrol et): {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Test etmek istediğin kitabı buraya yazabilirsin
    kitap_adi = "Ayıcık Kızgın Değil"
    print(f"'{kitap_adi}' internetten aranıyor ve veritabanına ekleniyor...")
    add_book_to_db(kitap_adi)