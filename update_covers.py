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

def is_cover_already_used(cursor, cover_url, current_book_id):
    """Veritabanında bu görselin başka bir kitapta kullanılıp kullanılmadığını kontrol eder."""
    if not cover_url:
        return False
    cursor.execute("SELECT COUNT(*) FROM books WHERE cover_url = ? AND id != ?", (cover_url, current_book_id))
    count = cursor.fetchone()[0]
    return count > 0

def fetch_cover_from_abm(title):
    try:
        search_url = f"https://www.abmyayinevi.com.tr/arama?q={requests.utils.quote(clean_title(title))}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(search_url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            img = soup.select_one(".product-item img, .product img, .image img, .prd-img img")
            if img:
                url = img.get("src") or img.get("data-src")
                if url:
                    if "http" not in url:
                        url = "https:" + url if url.startswith("//") else "https://www.abmyayinevi.com.tr" + url
                    return url
    except Exception:
        pass
    return None

def fetch_cover_from_kitapyurdu(title):
    try:
        search_url = f"https://www.kitapyurdu.com/index.php?route=product/search&filter_name={requests.utils.quote(clean_title(title))}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(search_url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            img = soup.select_one(".product-image img, .image img")
            if img:
                url = img.get("src") or img.get("data-src")
                if url:
                    clean_url = url.replace("getImage.php?image=", "").split("&")[0]
                    if "http" not in clean_url:
                        clean_url = "https:" + clean_url if clean_url.startswith("//") else "https://www.kitapyurdu.com" + clean_url
                    return clean_url
    except Exception:
        pass
    return None

def fetch_cover_from_dr(title):
    try:
        search_url = f"https://www.dr.com.tr/search?q={requests.utils.quote(clean_title(title))}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(search_url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            img = soup.select_one(".product-image img, .prd-img img, img.lazy")
            if img:
                return img.get("src") or img.get("data-src")
    except Exception:
        pass
    return None

def fetch_cover_from_tubitak(title):
    try:
        search_url = f"https://yayinlar.tubitak.gov.tr/arama?q={requests.utils.quote(clean_title(title))}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(search_url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            img = soup.select_one(".product-item img, .product img, img")
            if img:
                return img.get("src") or img.get("data-src")
    except Exception:
        pass
    return None

def fetch_cover_from_iskultur(title):
    try:
        search_url = f"https://www.iskultur.com.tr/catalogsearch/result/?q={requests.utils.quote(clean_title(title))}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(search_url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            img = soup.select_one(".product-image-photo, .product-image img")
            if img:
                return img.get("src") or img.get("data-src")
    except Exception:
        pass
    return None

def fetch_cover_from_yky(title):
    try:
        search_url = f"https://www.yapikrediyayinlari.com.tr/arama?q={requests.utils.quote(clean_title(title))}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(search_url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            img = soup.select_one(".product-item img, .book-image img, .cover img")
            if img:
                return img.get("src") or img.get("data-src")
    except Exception:
        pass
    return None

def update_database_covers():
    if not os.path.exists(DB_NAME):
        print(f"❌ '{DB_NAME}' veritabanı bulunamadı!")
        return

    con = sqlite3.connect(DB_NAME)
    cursor = con.cursor()
    
    # 1. Mükerrer (ortak) kapakları temizle
    cursor.execute("""
        UPDATE books 
        SET cover_url = '' 
        WHERE cover_url IN (
            SELECT cover_url FROM books 
            WHERE cover_url IS NOT NULL AND cover_url != '' 
            GROUP BY cover_url 
            HAVING COUNT(*) > 1
        )
    """)
    con.commit()

    # 2. Hatalı veya boş kapakları sıfırla
    cursor.execute("UPDATE books SET cover_url = '' WHERE cover_url IS NULL OR cover_url = '' OR cover_url LIKE '%longitood.com%' OR cover_url LIKE '%dogada-bir-an%'")
    con.commit()

    cursor.execute("SELECT id, title, publisher FROM books WHERE cover_url IS NULL OR cover_url = ''")
    books = cursor.fetchall()
    
    print(f"🔍 Toplam {len(books)} adet eksik kapaklı kitap yayınevi kaynaklarına göre taranıyor...")
    updated = 0
    missing_books = []

    for book_id, title, publisher in books:
        print(f"Araniyor: {title} ({publisher or 'Bilinmiyor'})")
        cover_url = None
        pub_lower = str(publisher).lower()

        # Yayınevine özel öncelikli arama
        if "abm" in pub_lower:
            cover_url = fetch_cover_from_abm(title)
        elif "tübitak" in pub_lower:
            cover_url = fetch_cover_from_tubitak(title)
        elif "iş bankası" in pub_lower or "iş kültür" in pub_lower:
            cover_url = fetch_cover_from_iskultur(title)
        elif "yapı kredi" in pub_lower or "yky" in pub_lower:
            cover_url = fetch_cover_from_yky(title)

        # Genel kaynaklar
        if not cover_url:
            cover_url = fetch_cover_from_kitapyurdu(title)
            if cover_url and is_cover_already_used(cursor, cover_url, book_id):
                cover_url = None

        if not cover_url:
            cover_url = fetch_cover_from_dr(title)
            if cover_url and is_cover_already_used(cursor, cover_url, book_id):
                cover_url = None

        # Yedek denemeler
        if not cover_url and "abm" not in pub_lower:
            cover_url = fetch_cover_from_abm(title)
        if not cover_url and "tübitak" not in pub_lower:
            cover_url = fetch_cover_from_tubitak(title)
        if not cover_url and "iş" not in pub_lower:
            cover_url = fetch_cover_from_iskultur(title)
        if not cover_url and "yapı" not in pub_lower:
            cover_url = fetch_cover_from_yky(title)

        # Çift kontrol
        if cover_url and is_cover_already_used(cursor, cover_url, book_id):
            cover_url = None

        if cover_url:
            cursor.execute("UPDATE books SET cover_url = ? WHERE id = ?", (cover_url, book_id))
            con.commit()
            print("  ✅ Kapak bulundu ve kaydedildi!")
            updated += 1
        else:
            print("  ❌ Bulunamadı.")
            missing_books.append(f"• {title} ({publisher or 'Bilinmeyen Yayınevi'})")

    con.close()
    
    print(f"\n✨ İşlem tamamlandı! Toplam {updated} kitabın kapağı güncellendi.")
    
    if missing_books:
        print(f"\n⚠️ KAPAK BULUNAMAYAN EKSİK KİTAPLAR ({len(missing_books)} adet):")
        for mb in missing_books:
            print(mb)
    else:
        print("\n🎉 Harika! Tüm eksik kitapların kapakları başarıyla tamamlandı.")

if __name__ == "__main__":
    update_database_covers()