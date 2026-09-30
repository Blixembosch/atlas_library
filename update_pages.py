import re
import sqlite3
import requests

DB_NAME = "atlas_library.db"


def clean_title(title):
  """Arama için kitap adını sadeleştirir ve Türkçe karakterleri normalize eder."""
  if not title:
    return ""

  tr_map = {
      "İ": "I",
      "ı": "i",
      "Ş": "S",
      "ş": "s",
      "Ğ": "G",
      "ğ": "g",
      "Ü": "U",
      "ü": "u",
      "Ö": "O",
      "ö": "o",
      "Ç": "C",
      "ç": "c",
  }
  for k, v in tr_map.items():
    title = title.replace(k, v)

  title = re.sub(r"\(.*?\)", "", title)
  title = re.sub(r"\[.*?\]", "", title)
  title = re.sub(r"[^\w\s]", " ", title)
  return " ".join(title.split())


def fetch_pages_from_open_library(title):
  """1. Yöntem: Kapakları bulan Open Library arama mantığı ile sayfa arar."""
  cleaned = clean_title(title)
  if not cleaned.strip():
    return None

  search_url = f"https://openlibrary.org/search.json?title={requests.utils.quote(cleaned)}"
  try:
    response = requests.get(search_url, timeout=5)
    if response.status_code == 200:
      data = response.json()
      docs = data.get("docs", [])
      if docs:
        for doc in docs[:3]:
          pages = doc.get("number_of_pages_median")
          if pages:
            return int(pages)
  except Exception:
    pass
  return None


def fetch_pages_from_google_books(title):
  """2. Yöntem: Open Library bulamazsa Google Books API ile arar."""
  cleaned = clean_title(title)
  if not cleaned.strip():
    return None

  url = f"https://www.googleapis.com/books/v1/volumes?q={requests.utils.quote(cleaned)}"
  try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
      data = response.json()
      items = data.get("items", [])
      if items:
        for item in items[:3]:
          page_count = item.get("volumeInfo", {}).get("pageCount")
          if page_count and isinstance(page_count, int):
            return page_count
  except Exception:
    pass
  return None


def update_all_missing_pages():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute("SELECT id, title, page_count FROM books")
  all_books = cursor.fetchall()

  books_to_update = []
  for book_id, title, page_count in all_books:
    if page_count is None or str(page_count).strip() in ["", "-", "0", "None"]:
      books_to_update.append((book_id, title))

  print(
      f"Toplam {len(books_to_update)} adet sayfa sayısı eksik kitap için hibrit"
      " tarama başlatıldı...\n"
  )

  updated_count = 0
  for book_id, title in books_to_update:
    print(f"Aranan: {title}")

    # Önce Open Library'yi dene
    page_count = fetch_pages_from_open_library(title)

    # Open Library'de yoksa Google Books'u dene (Yedek güç)
    if not page_count:
      page_count = fetch_pages_from_google_books(title)

    if page_count:
      cursor.execute(
          "UPDATE books SET page_count = ? WHERE id = ?", (page_count, book_id)
      )
      conn.commit()
      print(f" -> Sayfa sayısı başarıyla bulundu: {page_count} sayfa ✅\n")
      updated_count += 1
    else:
      print(" -> Hiçbir kaynakta bulunamadı ❌\n")

  conn.close()
  print(
      f"İşlem tamamlandı! Toplam {updated_count} kitabın sayfa sayısı"
      " güncellendi."
  )


if __name__ == "__main__":
  update_all_missing_pages()