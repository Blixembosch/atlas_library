import os
import sqlite3
import re
import requests
from bs4 import BeautifulSoup

DB_NAME = "atlas_library.db"

def clean_title(title):
    if not title:
        return ""
    title = re.sub(r"\(.*?\)", "", title)
    title = re.sub(r"\[.*?\]", "", title)
    title = re.sub(r"[^\w\s]", " ", title)
    return " ".join(title.split()).lower()

def fetch_cover_from_tubitak_category(title):
    """TÜBİTAK Okul Öncesi Kitaplığı kategorisinden eşleşme arar."""
    try:
        url = "https://yayinlar.tubitak.gov.tr/kategori/okul-oencesi-kitapligi-71"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            items = soup.select(".product-item, .product, li.item")
            cleaned_target = clean_title(title)
            for item in items:
                img = item.select_one("img")
                title_tag = item.select_one(".product-title, h2, h3, a")
                if img and title_tag:
                    item_title = clean_title(title_tag.get_text())
                    if cleaned_target in item_title or item_title in cleaned_target:
                        return img.get("src") or img.get("data-src")
    except Exception:
        pass
    return None

def fetch_cover_from_iskultur_series(title):
    """İş Bankası Dünyayı Öğreniyorum serisi sayfasından arar."""
    try:
        url = "https://www.iskultur.com.tr/kitap/resimli-kitaplar/dunyayi-ogreniyorum"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            items = soup.select(".product-item, .item.product")
            cleaned_target = clean_title(title)
            for item in items:
                img = item.select_one("img")
                title_tag = item.select_one(".product-item-link, .product-name")
                if img and title_tag:
                    item_title = clean_title(title_tag.get_text())
                    if cleaned_target in item_title or item_title in cleaned_target:
                        return img.get("src") or img.get("data-src")
    except Exception:
        pass
    return None

def fetch_cover_from_iskultur(title):
    """İş Bankası Kültür Yayınları Genel Arama"""
    try:
        search_url = f"https://www.iskultur.com.tr/catalogsearch/result/?q={requests.utils.quote(clean_title(title))}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(search_url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            img = soup.select_one(".product-image-photo, .product-image img")
            if img:
                return img.get("src") or img.get("data-src")
    except Exception:
        pass
    return None

def fetch_cover_from_yky(title):
    """Yapı Kredi Yayınları Arama"""
    try:
        search_url = f"https://www.yapikrediyayinlari.com.tr/arama?q={requests.utils.quote(clean_title(title))}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(search_url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            img = soup.select_one(".product-item img, .book-image img")
            if img:
                return img.get("src") or img.get("data-src")
    except Exception:
        pass
    return None

def fetch_cover_from_kitapyurdu(title):
    """Kitapyurdu Arama"""
    try:
        search_url = f"https://www.kitapyurdu.com/index.php?route=product/search&filter_name={requests.utils.quote(clean_title(title))}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(search_url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            img = soup.select_one(".product-image img")
            if img:
                url = img.get("src") or img.get("data-src")
                if url:
                    return url.replace("getImage.php?image=", "").split("&")[0]
    except Exception:
        pass
    return None

def fetch_cover_from_open_library(title):
    """Open Library Küresel Veritabanı"""
    try:
        cleaned = clean_title(title)
        if not cleaned.strip():
            return None
        search_url = f"https://openlibrary.org/search.json?title={requests.utils.quote(cleaned)}"
        res = requests.get(search_url, timeout=5)
        if res.status_code == 200:
            docs = res.json().get("docs", [])
            if docs:
                for doc in docs[:3]:
                    if doc.get("cover_i"):
                        return f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-L.jpg"
                    if doc.get("isbn"):
                        return f"https://covers.openlibrary.org/b/isbn/{doc.get('isbn')[0]}-L.jpg"
    except Exception:
        pass
    return None

def update_database_covers():
    if not os.path.exists(DB_NAME):
        print(f"❌ '{DB_NAME}' veritabanı bulunamadı!")
        return

    con = sqlite3.connect(DB_NAME)
    cursor = con.cursor()
    
    # Bozuk veya longitood linklerini temizleyip boşalt (böylece onlar da taranacaklar listesine girer)
    cursor.execute("UPDATE books SET cover_url = '' WHERE cover_url IS NULL OR cover_url = '' OR cover_url LIKE '%longitood.com%'")
    con.commit()

    # Sadece kapağı olmayan (boş olan) kitapları seçiyoruz
    cursor.execute("SELECT id, title, publisher FROM books WHERE cover_url IS NULL OR cover_url = ''")
    books = cursor.fetchall()
    
    print(f"🔍 Toplam {len(books)} adet eksik kapaklı kitap taranıyor (Mevcut kapaklılara dokunulmuyor)...")
    updated = 0

    for book_id, title, publisher in books:
        print(f"Araniyor: {title} ({publisher or 'Bilinmiyor'})")
        cover_url = None

        # 1. TÜBİTAK Özel Kategori Taraması
        cover_url = fetch_cover_from_tubitak_category(title)
        
        # 2. İş Bankası Dünyayı Öğreniyorum Serisi Taraması
        if not cover_url:
            cover_url = fetch_cover_from_iskultur_series(title)

        # 3. Yayınevine Özel Genel Arama (İşkültür veya YKY)
        pub_lower = str(publisher).lower()
        if not cover_url and ("iş bankası" in pub_lower or "iş kültür" in pub_lower):
            cover_url = fetch_cover_from_iskultur(title)
        elif not cover_url and ("yapı kredi" in pub_lower or "yky" in pub_lower):
            cover_url = fetch_cover_from_yky(title)

        # 4. Kitapyurdu
        if not cover_url:
            cover_url = fetch_cover_from_kitapyurdu(title)

        # 5. Diğer Yayınevi Genel Arama Yedekleri
        if not cover_url:
            cover_url = fetch_cover_from_iskultur(title)
        if not cover_url:
            cover_url = fetch_cover_from_yky(title)

        # 6. Open Library Küresel Veritabanı
        if not cover_url:
            cover_url = fetch_cover_from_open_library(title)

        if cover_url:
            cursor.execute("UPDATE books SET cover_url = ? WHERE id = ?", (cover_url, book_id))
            con.commit()
            print("  ✅ Kapak bulundu ve DB'ye kaydedildi!")
            updated += 1
        else:
            print("  ❌ Bulunamadı.")

    con.close()
    print(f"\n✨ İşlem tamamlandı! Toplam {updated} kitabın kapağı güncellendi.")

if __name__ == "__main__":
    update_database_covers()