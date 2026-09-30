import sqlite3
import re
import requests

DB_NAME = "atlas_library.db"


def clean_title(title):
  """Arama için kitap adını sadeleştirir."""
  if not title:
    return ""
  title = re.sub(r"\(.*?\)", "", title)
  title = re.sub(r"\[.*?\]", "", title)
  title = re.sub(r"[^\w\s]", " ", title)
  return " ".join(title.split())


def fetch_cover_from_open_library(title):
  """Open Library Search API kullanarak kitap adından kapak ID'si (cover_i) bulur."""
  cleaned = clean_title(title)
  if not cleaned.strip():
    return None

  # 1. Adım: Open Library Kitap Arama API'si
  search_url = f"https://openlibrary.org/search.json?title={requests.utils.quote(cleaned)}"

  try:
    response = requests.get(search_url, timeout=5)
    if response.status_code == 200:
      data = response.json()
      docs = data.get("docs", [])
      if docs:
        # İlk eşleşen kitabın kapak ID'sini (cover_i) veya ISBN'ini arayalım
        for doc in docs[:3]:  # İlk 3 sonuca bakalım
          cover_i = doc.get("cover_i")
          if cover_i:
            # Open Library'nin standart kapak görseli URL formatı (L = Large/Büyük boy)
            return f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"

          # Eğer cover_i yoksa ISBN ile deneyelim
          isbns = doc.get("isbn")
          if isbns:
            isbn = isbns[0]
            return f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
  except Exception as e:
    pass

  return None


def update_all_missing_covers():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute(
      "SELECT id, title FROM books WHERE cover_url IS NULL OR cover_url = ''"
  )
  books_to_update = cursor.fetchall()

  print(
      f"Toplam {len(books_to_update)} eksik kapaklı kitap için Open Library"
      " taraması başlatıldı..."
  )

  updated_count = 0
  for book_id, title in books_to_update:
    print(f"Aranan: {title}")
    cover_url = fetch_cover_from_open_library(title)

    if cover_url:
      cursor.execute(
          "UPDATE books SET cover_url = ? WHERE id = ?", (cover_url, book_id)
      )
      conn.commit()
      print(" -> Open Library'den kapak bulundu ve eklendi! ✅")
      updated_count += 1
    else:
      print(" -> Bulunamadı ❌")

  conn.close()
  print(
      f"\nİşlem tamamlandı! Toplam {updated_count} kitabın kapağı güncellendi."
  )


if __name__ == "__main__":
  update_all_missing_covers()