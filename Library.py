from datetime import date, datetime, timedelta
import html
import os
from pathlib import Path
import random
import shutil  # V0.9 CHANGE: DB geri yükleme
import sqlite3
import tempfile  # V0.9 CHANGE: DB geri yükleme
import uuid
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Atlas'ın Sihirli Kütüphanesi", page_icon="🏰", layout="wide"
)

DB_NAME = "atlas_library.db"
BASE = Path(__file__).parent
SEED = BASE / "data" / "books.csv"
TZ = ZoneInfo("Europe/Amsterdam")

# --- CSS STİLLERİ ---
st.markdown(
    """
<style>
:root{--primary:#4F7CFF;--secondary:#7C4DFF;--r-card:24px;--r-btn:14px;--shadow:0 4px 20px rgba(0,0,0,.06);}
header[data-testid="stHeader"]{background:transparent!important;height:0!important;}
.block-container{padding:.8rem 1.2rem 1.5rem!important;max-width:1400px;}
.stApp{background:#F8FAFC!important;color:#1e293b;}
section[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e2e8f0;}

/* Buttons */
div.stButton>button{border-radius:var(--r-btn);font-weight:700;color:#fff!important;border:none;
  background:linear-gradient(135deg,var(--primary),var(--secondary));
  box-shadow:0 4px 14px rgba(79,124,255,.25);padding:.55rem .8rem;transition:.2s;}
div.stButton>button:hover{transform:translateY(-2px);filter:brightness(1.07);}

/* Sidebar */
.side-logo{text-align:center;padding:10px 0 4px;}
.side-logo-emoji{font-size:2.2rem;line-height:1.1;}
.side-logo-title{font-weight:800;font-size:.95rem;color:#1e293b;}
.side-logo-sub{font-size:.7rem;color:#64748b;}
.side-label{font-size:.68rem;letter-spacing:.12em;color:#94a3b8;font-weight:800;margin:16px 0 6px;}
.side-card{display:flex;justify-content:space-between;align-items:center;background:#F8FAFC;
  border-radius:var(--r-btn);padding:9px 14px;margin-bottom:6px;font-size:.85rem;font-weight:700;color:#475569;}
.side-card b{font-size:1.1rem;color:#1e293b;}
.side-ver{text-align:center;font-size:.65rem;color:#94a3b8;margin-top:8px;}
section[data-testid="stSidebar"] div.stButton>button{background:#fff;color:#1e293b!important;
  border:1px solid #e2e8f0;box-shadow:none;justify-content:flex-start;}
section[data-testid="stSidebar"] div.stButton>button:hover{border-color:var(--primary);color:var(--primary)!important;}

/* Hero */
.st-key-hero_box{background:linear-gradient(135deg,#4F7CFF 0%,#7C4DFF 100%);border-radius:var(--r-card);
  padding:14px 20px 10px;box-shadow:var(--shadow);margin-bottom:14px;}
/* V1.0 CHANGE: kompakt hero (hedef + seviye tek satırda) */
.hero-top{display:flex;flex-wrap:wrap;gap:10px 28px;align-items:center;justify-content:space-between;margin-bottom:8px;}
.hero-left{flex:1 1 280px;min-width:0;}
.hero-right{flex:0 1 260px;min-width:200px;color:#fff;font-size:.85rem;}
.hero-right .xp-track{height:8px;margin:4px 0 2px;}
.hero-right .xp-text{color:#fff;opacity:.9;font-size:.75rem;}
.hero-goalline{display:flex;align-items:center;gap:10px;flex-wrap:wrap;color:#fff;margin:2px 0;}
.hero-goalline b{font-size:.95rem;}
.hero-title{font-size:1.35rem;font-weight:900;color:#fff;margin-bottom:2px;}
.hero-sub{color:#fff;opacity:.95;margin:0 0 12px;font-weight:500;font-size:.95rem;}
.hero-xp{color:#fff;font-size:.9rem;margin-bottom:14px;}
.hero-right .xp-track{background:rgba(255,255,255,.3);}
.hero-right .xp-fill{background:#fff;}

/* V0.9 CHANGE: günlük hedef göstergesi */
.goal-row{background:rgba(255,255,255,.16);border-radius:18px;padding:12px 16px;margin-bottom:14px;color:#fff;}
.goal-label{font-weight:800;font-size:1rem;margin-bottom:8px;}
.goal-slots{display:flex;gap:6px;}
.goal-slot{width:30px;height:30px;border-radius:50%;border:2px dashed rgba(255,255,255,.7);
  display:flex;align-items:center;justify-content:center;font-size:.9rem;}
.goal-slot.done{background:#fff;border:2px solid #fff;}
.goal-slot.wait{background:rgba(255,255,255,.3);border:2px solid rgba(255,255,255,.8);}
.goal-msg{font-size:.82rem;font-weight:600;color:#fff;opacity:.95;}
.goal-streak{display:inline-block;background:#fff;color:#F97316;border-radius:99px;
  padding:1px 10px;font-weight:800;font-size:.78rem;}
.st-key-hero_box div.stButton>button{background:#fff;color:#4F7CFF!important;box-shadow:none;}

/* XP bar */
.xp-track{background:#e2e8f0;border-radius:99px;height:12px;overflow:hidden;margin:6px 0 4px;}
.xp-fill{background:linear-gradient(90deg,#4F7CFF,#7C4DFF);height:100%;border-radius:99px;}
.xp-text{font-size:.8rem;font-weight:600;}

/* Category cards */
div[class*="st-key-cat_"] button,div[class*="st-key-catON_"] button{background:#fff;color:#1e293b!important;
  border:1px solid #e2e8f0;border-radius:16px;box-shadow:var(--shadow);min-height:64px;padding:6px 8px !important;white-space:normal;}
div[class*="st-key-cat_"] button p,div[class*="st-key-catON_"] button p{margin:0;line-height:1.2;font-size:0.82rem;}
div[class*="st-key-catON_"] button{border:2px solid #4F7CFF;}

/* Book cards */
.book-card{background:#fff;border-radius:var(--r-card);padding:12px;box-shadow:var(--shadow);border:1px solid #eef2f7;
  display:flex;flex-direction:column;align-items:center;text-align:center;overflow:hidden;position:relative;margin-bottom:6px;}
.book-cover{width:100%;display:flex;align-items:center;justify-content:center;background:#F1F5F9;border-radius:18px;overflow:hidden;}
.book-cover img{height:100%;max-width:100%;object-fit:contain;}
.book-badge{position:absolute;top:18px;left:18px;background:#fff;border-radius:99px;padding:3px 10px;
  font-size:.72rem;font-weight:800;color:#7C4DFF;box-shadow:0 2px 8px rgba(0,0,0,.12);}
.school-badge{position:absolute;top:18px;right:18px;background:#FEF3C7;border-radius:99px;padding:3px 10px;
  font-size:.7rem;font-weight:800;color:#D97706;box-shadow:0 2px 8px rgba(0,0,0,.08);}
.book-title{font-weight:800;font-size:.98rem;line-height:1.25;margin:10px 0 6px;height:2.5em;overflow:hidden;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;}
.book-meta{font-size:.8rem;color:#64748b;line-height:1.7;}

/* Recent adventures */
.recent-item{background:#fff;border-radius:18px;padding:12px 18px;margin-bottom:8px;box-shadow:var(--shadow);
  display:flex;justify-content:space-between;}
.recent-item span{color:#94a3b8;font-size:.8rem;}

/* Journey */
.journey{display:flex;gap:10px;overflow-x:auto;padding:6px 2px 14px;}
.stop{flex:1;min-width:112px;border-radius:20px;padding:14px 8px;text-align:center;font-weight:800;border:2px solid;background:#fff;}
.stop-icon{font-size:2rem;}
.stop small{display:block;font-weight:600;font-size:.7rem;margin-top:4px;}
.stop.done{background:#ECFDF5;border-color:#22C55E;color:#15803D;}
.stop.now{background:#EEF3FF;border-color:#4F7CFF;color:#4F7CFF;box-shadow:0 0 0 4px rgba(79,124,255,.15);}
.stop.lock{background:#F1F5F9;border-color:#E2E8F0;color:#94A3B8;}

.stat-card{background:#fff;border-radius:var(--r-card);padding:18px;box-shadow:var(--shadow);margin-bottom:14px;}
.stat-card small{color:#64748b;font-weight:800;}
.stat-val{font-size:2rem;font-weight:900;color:#4F7CFF;}
.cat-box{background:#fff;border-radius:var(--r-card);padding:16px;box-shadow:var(--shadow);}

/* V0.9 CHANGE: dil özeti kartları */
.lang-card{background:#fff;border-radius:var(--r-card);padding:16px 18px;box-shadow:var(--shadow);margin-bottom:14px;}
.lang-title{font-weight:800;font-size:1.05rem;margin-bottom:10px;}
.lang-row{display:flex;gap:10px;}
.lang-row div{flex:1;text-align:center;background:#F8FAFC;border-radius:16px;padding:10px 4px;}
.lang-row b{display:block;font-size:1.6rem;font-weight:900;color:#4F7CFF;}
.lang-row span{font-size:.75rem;color:#64748b;font-weight:700;}
</style>
""",
    unsafe_allow_html=True,
)

ADMIN_CSS = """
<style>
div.stButton>button,div.stFormSubmitButton>button{background:#1E293B;color:#fff!important;border-radius:8px;box-shadow:none;border:none;}
div.stButton>button:hover{transform:none;background:#334155;}
[data-testid="stMetric"]{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:14px 18px;box-shadow:0 1px 3px rgba(0,0,0,.04);}
.stTabs [data-baseweb="tab"]{font-weight:600;}
.admin-head{border-bottom:1px solid #e2e8f0;margin-bottom:16px;padding-bottom:8px;}
.admin-head h2{margin:0;font-size:1.4rem;color:#0F172A;}
.admin-head p{margin:0;color:#64748b;font-size:.85rem;}
</style>
"""


# V1.0 CHANGE: tek kategori listesi (ana sayfa, kütüphane ve yönetici formları kullanır)
CATEGORIES = [
    "Hikaye", "Bilgi & Keşif", "Aktivite", "İlk Okuma",
    "Doğa & Hayvanlar", "Bilim", "Değerler",
]

# V1.0 CHANGE: kitap isimleri internette araştırılarak yapılan kategori incelemesi.
# Yalnızca değişecek kitaplar: kitap_id -> (yeni kategori, gerekçe, güven)
CATEGORY_REVIEW = {
    "BÇ-1": ("Bilgi & Keşif", "Resimli sözlük / dil kitabı", "yüksek"),
    "BÇ-3": ("Bilgi & Keşif", "Biyografi (Galileo)", "yüksek"),
    "BÇ-4": ("Hikaye", "Jules Verne uyarlaması, kurgu", "yüksek"),
    "BÇ-5": ("Bilgi & Keşif", "Ressam tanıtım serisi (sanat bilgisi)", "yüksek"),
    "BÇ-6": ("Aktivite", "Satranç öğreten etkileşimli kitap", "yüksek"),
    "BÇ-9": ("Hikaye", "Minik Ayıcıklar: hayvan karakterli kurgu hikâye", "yüksek"),
    "BÇ-10": ("Hikaye", "Minik Ayıcıklar: hayvan karakterli kurgu hikâye", "yüksek"),
    "BÇ-11": ("Hikaye", "Minik Ayıcıklar: hayvan karakterli kurgu hikâye", "yüksek"),
    "BÇ-12": ("Hikaye", "Minik Ayıcıklar: hayvan karakterli kurgu hikâye", "yüksek"),
    "BÇ-13": ("Bilgi & Keşif", "Ressam tanıtım serisi (sanat bilgisi)", "yüksek"),
    "BÇ-17": ("Bilgi & Keşif", "Ressam tanıtım serisi (sanat bilgisi)", "yüksek"),
    "BÇ-18": ("Değerler", "Günlük alışkanlık / beslenme teması", "yüksek"),
    "ABM-7": ("Hikaye", "Kurgu hikâye (kuş karakteri)", "orta"),
    "ABM-8": ("Bilgi & Keşif", "Finansal okuryazarlık bilgi kitabı", "yüksek"),
    "ABM-15": ("Değerler", "Yemek/günlük yaşam alışkanlığı", "orta"),
    "ABM-22": ("Aktivite", "Düğmeli etkileşimli aktivite kitabı (kitapyurdu yorumları)", "yüksek"),
    "ABM-27": ("Aktivite", "Yoga hareketleri, etkinlik", "yüksek"),
    "AK-1": ("Hikaye", "Hayvan karakterli kurgu hikâye", "yüksek"),
    "AK-2": ("Hikaye", "Hayvan karakterli kurgu hikâye", "yüksek"),
    "AK-4": ("Hikaye", "İlk Okuma yalnızca Cin Ali serisi; kitap doğrulanamadı", "düşük"),
    "AK-5": ("Değerler", "Peter H. Reynolds: yaratıcılık/cesaret teması", "yüksek"),
    "AR-1": ("Hikaye", "Masal derlemesi", "yüksek"),
    "BY-1": ("Değerler", "Tuvalet alışkanlığı, günlük yaşam", "yüksek"),
    "BTK-1": ("Bilgi & Keşif", "Finansal okuryazarlık", "yüksek"),
    "BTK-2": ("Bilgi & Keşif", "Finansal okuryazarlık", "yüksek"),
    "CÇ-1": ("Hikaye", "Hayvan karakterli kurgu hikâye", "yüksek"),
    "DK-7": ("Hikaye", "Mr. Men / Little Miss serisi: karakter hikâyesi", "yüksek"),
    "DK-8": ("Hikaye", "Mr. Men / Little Miss serisi: karakter hikâyesi", "yüksek"),
    "DK-10": ("Hikaye", "Mr. Men / Little Miss serisi: karakter hikâyesi", "yüksek"),
    "DK-21": ("Hikaye", "Mr. Men / Little Miss serisi: karakter hikâyesi", "yüksek"),
    "DK-23": ("Hikaye", "Mr. Men / Little Miss serisi: karakter hikâyesi", "yüksek"),
    "DK-24": ("Hikaye", "Mr. Men / Little Miss serisi: karakter hikâyesi", "yüksek"),
    "DK-26": ("Hikaye", "Mr. Men / Little Miss serisi: karakter hikâyesi", "yüksek"),
    "DO-1": ("Hikaye", "Hayvanlı mizahi resimli kitap (kitapyurdu)", "yüksek"),
    "DO-3": ("Bilgi & Keşif", "Atlas: coğrafya / kültür", "yüksek"),
    "DO-5": ("Bilgi & Keşif", "Dahiler Sınıfı: biyografi serisi (internetten doğrulandı)", "yüksek"),
    "DO-6": ("Bilgi & Keşif", "Dahiler Sınıfı: biyografi serisi (internetten doğrulandı)", "yüksek"),
    "DO-7": ("Bilgi & Keşif", "Dahiler Sınıfı: biyografi serisi (internetten doğrulandı)", "yüksek"),
    "DO-8": ("Bilgi & Keşif", "Dahiler Sınıfı: biyografi serisi (internetten doğrulandı)", "yüksek"),
    "DO-9": ("Bilgi & Keşif", "Dahiler Sınıfı: biyografi serisi (internetten doğrulandı)", "yüksek"),
    "DO-10": ("Bilgi & Keşif", "Dahiler Sınıfı: biyografi serisi (internetten doğrulandı)", "yüksek"),
    "DO-11": ("Bilgi & Keşif", "Dahiler Sınıfı: biyografi serisi (internetten doğrulandı)", "yüksek"),
    "DO-13": ("Bilgi & Keşif", "Meslek tanıtımı", "yüksek"),
    "DO-28": ("Bilgi & Keşif", "Genel bilgi (yer altı / su altı)", "orta"),
    "HK-1": ("Hikaye", "Kurgu hikâye", "orta"),
    "KKÇ-3": ("Bilgi & Keşif", "Atatürk serisi: tarih / bilgi", "yüksek"),
    "KKÇ-4": ("Bilgi & Keşif", "Atatürk serisi: tarih / bilgi", "yüksek"),
    "NC-1": ("Doğa & Hayvanlar", "Doğa temalı resimli sözlük", "yüksek"),
    "RH-1": ("Hikaye", "Resimli hikâye (başlıktan; doğrulanamadı)", "orta"),
    "RH-9": ("Bilgi & Keşif", "Genel bilgi", "orta"),
    "RH-10": ("Hikaye", "Sessiz kitap, kurgu (kitapyurdu: Hikâye)", "yüksek"),
    "RH-11": ("Hikaye", "Hayvan/insan karakterli kurgu hikâye", "orta"),
    "RH-12": ("Hikaye", "Hayvan/insan karakterli kurgu hikâye", "orta"),
    "RH-13": ("Hikaye", "Hayvan/insan karakterli kurgu hikâye", "orta"),
    "RH-15": ("Hikaye", "Hayvan/insan karakterli kurgu hikâye", "orta"),
    "RH-16": ("Hikaye", "Hayvan/insan karakterli kurgu hikâye", "orta"),
    "RH-17": ("Hikaye", "Hayvan/insan karakterli kurgu hikâye", "orta"),
    "RH-18": ("Hikaye", "Hayvan/insan karakterli kurgu hikâye", "orta"),
    "RH-19": ("Değerler", "Sorumluluk temalı bahar öyküsü (kitapyurdu)", "yüksek"),
    "RH-24": ("Hikaye", "Hayvan/insan karakterli kurgu hikâye", "orta"),
    "RH-25": ("Hikaye", "Resimli hikâye (kitapyurdu: Hikâye)", "yüksek"),
    "STU-1": ("Aktivite", "Ara-bul (zoek boek) etkinlik kitabı", "yüksek"),
    "TB-2": ("Doğa & Hayvanlar", "TÜBİTAK doğa resimli kitabı; doğrulanamadı", "düşük"),
    "TB-7": ("Bilim", "Dağların oluşumu: jeoloji bilgisi", "orta"),
    "TB-14": ("Doğa & Hayvanlar", "Gece hayvanları: bilgilendirici (kitapyurdu)", "yüksek"),
    "TB-18": ("Doğa & Hayvanlar", "İmparator penguen yumurtası: doğa", "orta"),
    "TB-23": ("Doğa & Hayvanlar", "Kuzey Kutbu: bilgilendirici doğa kitabı (kitapyurdu)", "yüksek"),
    "TİB-3": ("Doğa & Hayvanlar", "Orman: doğa bilgisi", "yüksek"),
    "TİB-4": ("Hikaye", "Hayvan karakterli kurgu hikâye", "yüksek"),
    "TİB-5": ("Bilgi & Keşif", "Genel bilgi", "yüksek"),
    "TİB-7": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-8": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-9": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-10": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-11": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-12": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-13": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-14": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-15": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-16": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-17": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-18": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-19": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-20": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-21": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-22": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-23": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-24": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-25": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-26": ("Bilgi & Keşif", "Meslek tanıtım serisi", "yüksek"),
    "TİB-29": ("Doğa & Hayvanlar", "Doğa / hayvan bilgisi", "yüksek"),
    "TİB-30": ("Doğa & Hayvanlar", "Doğa / hayvan bilgisi", "yüksek"),
    "TİB-32": ("Bilgi & Keşif", "Günlük yaşam / uygarlık bilgisi", "yüksek"),
    "TİB-37": ("Doğa & Hayvanlar", "Doğa / hayvan bilgisi", "yüksek"),
    "TİB-38": ("Doğa & Hayvanlar", "Doğa / hayvan bilgisi", "yüksek"),
    "TİB-42": ("Bilgi & Keşif", "Günlük yaşam / uygarlık bilgisi", "yüksek"),
    "TİB-48": ("Değerler", "Diş fırçalama alışkanlığı", "yüksek"),
    "TİB-58": ("Hikaye", "İlk Okuma Kitabım serisi tek tipte Hikaye", "orta"),
    "TİB-60": ("Hikaye", "İlk Okuma Kitabım serisi tek tipte Hikaye", "orta"),
    "TİB-68": ("Doğa & Hayvanlar", "Hayvan tanıtım kitabı", "yüksek"),
    "TİB-73": ("Hikaye", "Hayvan karakterli kurgu hikâye", "orta"),
    "YKY-1": ("Bilgi & Keşif", "Genel bilgi (Büyük Sorular)", "yüksek"),
    "YKY-3": ("Doğa & Hayvanlar", "Böcek/doğa teması", "orta"),
    "YKY-7": ("Hikaye", "Kurgu hikâye", "orta"),
}


def akilli_kategori_belirle(title, author, subcategory=""):
  # V1.0 CHANGE: anahtar kelime tahmini ("kg", "dünya", "sayı"... hepsini Bilim yapıyordu)
  # kaldırıldı; yalnızca Cin Ali serisi İlk Okuma olarak kalır.
  t = str(title).lower()
  a = str(author).lower()
  sub = str(subcategory).lower()
  combined = f"{t} {a} {sub}"

  if "çin ali" in combined or "cin ali" in combined:
    return "İlk Okuma"

  return None


def fetch_book_by_isbn(isbn):
  """Open Library API kullanarak ISBN ile kitap bilgilerini çeker"""
  clean_isbn = "".join(filter(str.isalnum, str(isbn)))
  if not clean_isbn:
    return None
  try:
    url = f"https://openlibrary.org/isbn/{clean_isbn}.json"
    res = requests.get(url, timeout=5)
    if res.status_code == 200:
      data = res.json()
      title = data.get("title", "")
      # V0.9 CHANGE: sayfa bilgisi yoksa varsayılan (28) EKLEME, boş bırak
      pages = data.get("number_of_pages")

      # Yazar bilgisi
      author = "Bilinmiyor"
      authors_data = data.get("authors", [])
      if authors_data:
        author_key = authors_data[0].get("key")
        if author_key:
          author_res = requests.get(f"https://openlibrary.org{author_key}.json", timeout=3)
          if author_res.status_code == 200:
            author = author_res.json().get("name", "Bilinmiyor")

      # Yayınevi
      publishers = data.get("publishers", ["De Vuurvlinder"])
      publisher = publishers[0] if publishers else "De Vuurvlinder"

      # Kapak resmi
      covers = data.get("covers", [])
      cover_url = f"https://covers.openlibrary.org/b/id/{covers[0]}-L.jpg" if covers else ""

      return {
          "title": title,
          "author": author,
          "publisher": publisher,
          "pages": int(pages) if pages else None,  # V0.9 CHANGE
          "cover_url": cover_url,
          "isbn": clean_isbn
      }
  except Exception:
    pass
  return None


# V0.9 CHANGE: kapak yerine kullanılmaması gereken görseller (tek yerden yönetilir)
BAD_COVER_MARKERS = ("longitood.com", "deneyap-logo")


def _is_bad_cover(url):
  return any(m in str(url) for m in BAD_COVER_MARKERS)


def db():
  con = sqlite3.connect(DB_NAME, check_same_thread=False)
  con.row_factory = sqlite3.Row
  con.executescript(
      "CREATE TABLE IF NOT EXISTS books(id TEXT PRIMARY KEY,title TEXT NOT"
      " NULL,publisher TEXT,pages INTEGER,author TEXT,isbn TEXT,age"
      " TEXT,category TEXT,subcategory TEXT,cover_url TEXT,language TEXT"
      " DEFAULT 'Türkçe',read_count INTEGER DEFAULT 0,created_at TEXT,"
      " is_school INTEGER DEFAULT 0, is_outgrown INTEGER DEFAULT 0); "
      "CREATE TABLE IF NOT EXISTS reading_log(id INTEGER PRIMARY KEY"
      " AUTOINCREMENT,book_id TEXT,status TEXT,read_at TEXT,cycle INTEGER"
      " DEFAULT 1); "
      # V0.9 CHANGE: günlük hedef gibi ayarlar için
      "CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);"
  )

  cursor = con.cursor()
  cursor.execute("PRAGMA table_info(books)")
  columns = [col["name"] for col in cursor.fetchall()]
  if "language" not in columns:
    cursor.execute("ALTER TABLE books ADD COLUMN language TEXT DEFAULT 'Türkçe'")
    con.commit()
  if "is_school" not in columns:
    cursor.execute("ALTER TABLE books ADD COLUMN is_school INTEGER DEFAULT 0")
    con.commit()
  # V1.0 CHANGE: yaşı geçen kitaplar için bayrak (öneri havuzundan çıkar)
  if "is_outgrown" not in columns:
    cursor.execute("ALTER TABLE books ADD COLUMN is_outgrown INTEGER DEFAULT 0")
    con.commit()

  if con.execute("select count() from books").fetchone()[0] == 0:
    SEED.parent.mkdir(parents=True, exist_ok=True)
    if SEED.exists():
      df = pd.read_csv(SEED, dtype=str).fillna("")
      df["created_at"] = datetime.now(TZ).isoformat()
      df["read_count"] = 0
      df["is_school"] = 0
      if "language" not in df.columns:
        df["language"] = "Türkçe"
      if "cover_url" in df.columns:
        df["cover_url"] = df["cover_url"].apply(
            lambda x: "" if _is_bad_cover(x) else x  # V0.9 CHANGE
        )

      def apply_smart_cat(row):
        smart = akilli_kategori_belirle(
            row.get("title", ""),
            row.get("author", ""),
            row.get("subcategory", ""),
        )
        return smart if smart else row.get("category", "Hikaye")

      df["category"] = df.apply(apply_smart_cat, axis=1)
      df.to_sql("books", con, if_exists="append", index=False)
      con.commit()
  else:
    con.execute(
        "UPDATE books SET cover_url = '' WHERE cover_url LIKE"
        " '%longitood.com%'"
    )
    # V0.9 CHANGE: kapak yerine konmuş site logosunu temizle
    con.execute(
        "UPDATE books SET cover_url = '' WHERE cover_url LIKE '%deneyap-logo%'"
    )
    # V0.9 CHANGE: okul kitapları her zaman Dutch
    con.execute(
        "UPDATE books SET language = 'Dutch' WHERE is_school = 1"
        " AND (language IS NULL OR language != 'Dutch')"
    )
    con.commit()

  # V1.0 CHANGE: kategori artık her açılışta ezilmez; yönetici seçimi kalıcıdır.
  con.execute("UPDATE books SET category = 'İlk Okuma' WHERE category IS NULL OR category = ''")
  con.commit()

  return con


db()


def rows(table):
  con = db()
  r = [dict(x) for x in con.execute(f"select * from {table}").fetchall()]
  con.close()
  return r


def cover(url):
  if not url or str(url).strip() == "" or str(url).lower() == "nan":
    return None
  if _is_bad_cover(url):  # V0.9 CHANGE
    return None
  return str(url).strip()


def get_books_df():
  con = sqlite3.connect(DB_NAME)
  df = pd.read_sql("SELECT * FROM books", con)
  con.close()
  if "read_count" not in df.columns:
    df["read_count"] = 0
  else:
    df["read_count"] = pd.to_numeric(df["read_count"], errors="coerce").fillna(0)
  if "language" not in df.columns:
    df["language"] = "Türkçe"
  if "is_school" not in df.columns:
    df["is_school"] = 0
  # V0.9 CHANGE: sayfa boşsa NaN kalsın (varsayılan yok), okul bayrağı her zaman 0/1
  df["pages"] = pd.to_numeric(df["pages"], errors="coerce")
  df["is_school"] = pd.to_numeric(df["is_school"], errors="coerce").fillna(0).astype(int)
  # V1.0 CHANGE: yaşı geçti bayrağı
  if "is_outgrown" not in df.columns:
    df["is_outgrown"] = 0
  df["is_outgrown"] = pd.to_numeric(df["is_outgrown"], errors="coerce").fillna(0).astype(int)
  return df


books_df = get_books_df()
# V0.9 CHANGE: okuldan gelen kitaplar kütüphanede durmaz; sadece sayımlara girer
home_df = books_df[books_df["is_school"] == 0]
# V1.0 CHANGE: öneri/kategori sayaçları sadece yaşına uygun kitapları sayar
eligible_df = home_df[home_df["is_outgrown"] == 0]

if "selected_category" not in st.session_state:
  st.session_state.selected_category = "Tümü"
if "current_featured_books" not in st.session_state:
  st.session_state.current_featured_books = []
if "admin_logged_in" not in st.session_state:
  st.session_state.admin_logged_in = False
if "nav_page" not in st.session_state:
  st.session_state.nav_page = "Ana Sayfa"
if "home_active_category" not in st.session_state:
  st.session_state.home_active_category = "Tümü"
if "featured_note" not in st.session_state:  # V0.9 CHANGE
  st.session_state.featured_note = ""
if "goal_celebrated" not in st.session_state:  # V0.9 CHANGE
  st.session_state.goal_celebrated = ""


# XP / Seviye Sistem Fonksiyonları
def calculate_level(total_read_books):
  xp = total_read_books * 10
  level = xp // 100 + 1
  in_level = xp % 100
  return {"xp": xp, "level": level, "pct": in_level, "to_next": 100 - in_level}


def level_bar_html(lv):
  return (
      f'<div class="xp-track"><div class="xp-fill" style="width:{lv["pct"]}%"></div></div>'
      f'<div class="xp-text">Seviye {lv["level"] + 1}\'e {lv["to_next"]} XP kaldı</div>'
  )


# V0.9 CHANGE: okul kitapları da okunmuş sayılır (XP, rozet, yolculuk)
total_read_books = int((books_df["read_count"] > 0).sum())
lvl = calculate_level(total_read_books)


# V0.9 CHANGE: Türkçe / Dutch okuma özeti (her okuma kaydı kitabın diline göre sayılır)
def language_read_summary(logs, books):
  lang_of = dict(zip(books["id"], books["language"].fillna("Türkçe")))
  now = datetime.now(TZ)
  out = {}
  for l in logs:
    lang = lang_of.get(l.get("book_id"))
    if lang is None:  # silinmiş kitabın eski kaydı
      continue
    group = lang if lang in ("Türkçe", "Dutch") else "Diğer"
    row = out.setdefault(group, {"total": 0, "year": 0, "month": 0})
    row["total"] += 1
    try:
      dt = datetime.fromisoformat(l.get("read_at"))
    except (TypeError, ValueError):
      continue
    if dt.year == now.year:
      row["year"] += 1
      if dt.month == now.month:
        row["month"] += 1
  return out


def lang_card_html(title, d):
  d = d or {"month": 0, "year": 0, "total": 0}
  return (
      f'<div class="lang-card"><div class="lang-title">{title}</div><div class="lang-row">'
      f'<div><b>{d["month"]}</b><span>Bu Ay</span></div>'
      f'<div><b>{d["year"]}</b><span>Bu Yıl</span></div>'
      f'<div><b>{d["total"]}</b><span>Toplam</span></div></div></div>'
  )


# V0.9 CHANGE: veritabanı geri yükleme (yönetici paneli > DB Yedek)
PRE_RESTORE_PATH = Path("data") / "pre_restore.db"  # data/*.db zaten .gitignore'da


def summarize_db(path):
  """Dosya geçerli bir Atlas veritabanıysa {'books','logs','pending'} döner, değilse None."""
  try:
    con = sqlite3.connect(path)
    try:
      if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        return None
      tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
      if not {"books", "reading_log"} <= tables:
        return None
      bcols = {r[1] for r in con.execute("PRAGMA table_info(books)")}
      lcols = {r[1] for r in con.execute("PRAGMA table_info(reading_log)")}
      if not ({"id", "title"} <= bcols and {"book_id", "read_at"} <= lcols):
        return None
      pending = (
          con.execute("SELECT count(*) FROM reading_log WHERE status = 'pending'").fetchone()[0]
          if "status" in lcols
          else 0
      )
      return {
          "books": con.execute("SELECT count(*) FROM books").fetchone()[0],
          "logs": con.execute("SELECT count(*) FROM reading_log").fetchone()[0],
          "pending": pending,
      }
    finally:
      con.close()
  except sqlite3.Error:
    return None


def _write_temp_db(data):
  tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
  tmp.write(data)
  tmp.close()
  return tmp.name


def inspect_backup(data):
  """Yüklenen dosyayı geçici kopyada doğrular. (özet, hata_mesajı) döner."""
  if not data.startswith(b"SQLite format 3\x00"):
    return None, "Bu dosya bir SQLite veritabanı değil. İndirdiğin atlas_library.db dosyasını seç."
  tmp = _write_temp_db(data)
  try:
    info = summarize_db(tmp)
  finally:
    os.remove(tmp)
  if info is None:
    return None, "Dosya bozuk ya da Atlas veritabanı değil (books / reading_log tabloları bulunamadı)."
  return info, None


def restore_db(data):
  """Önce mevcut DB'nin kopyasını alır, sonra yüklenen yedeği SQLite backup API ile yazar."""
  tmp = _write_temp_db(data)
  try:
    if os.path.exists(DB_NAME):
      PRE_RESTORE_PATH.parent.mkdir(parents=True, exist_ok=True)
      shutil.copyfile(DB_NAME, PRE_RESTORE_PATH)
    src = sqlite3.connect(tmp)
    dst = sqlite3.connect(DB_NAME)
    try:
      src.backup(dst)
    finally:
      src.close()
      dst.close()
  finally:
    os.remove(tmp)
  db().close()  # eski şemalı yedekler için eksik sütun/tabloları tamamlar


# V0.9 CHANGE: ayarlar (günlük hedef vb.)
def get_setting(key, default):
  con = sqlite3.connect(DB_NAME)
  r = con.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
  con.close()
  return r[0] if r else default


def set_setting(key, value):
  con = sqlite3.connect(DB_NAME)
  con.execute(
      "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value))
  )
  con.commit()
  con.close()


def daily_goal():
  try:
    return max(1, int(get_setting("daily_goal", "2")))
  except (TypeError, ValueError):
    return 2


# V0.9 CHANGE: okuma kaydı durumları. 'pending' = çocuk işaretledi, ebeveyn onayı bekliyor.
# Eski kayıtlarda status boş olabilir, onaylı sayılır.
def is_pending(log):
  return log.get("status") == "pending"


def approved_logs(logs):
  return [l for l in logs if not is_pending(l)]


def approve_reading(log_id):
  con = sqlite3.connect(DB_NAME)
  row = con.execute(
      "SELECT book_id, status FROM reading_log WHERE id = ?", (log_id,)
  ).fetchone()
  if row and row[1] == "pending":
    con.execute("UPDATE reading_log SET status = 'read' WHERE id = ?", (log_id,))
    con.execute(
        "UPDATE books SET read_count = read_count + 1 WHERE id = ?", (row[0],)
    )
    con.commit()
  con.close()


def reject_reading(log_id):
  con = sqlite3.connect(DB_NAME)
  con.execute("DELETE FROM reading_log WHERE id = ? AND status = 'pending'", (log_id,))
  con.commit()
  con.close()


def goal_status():
  """Bugünün hedefi: onaylanan, bekleyen, kalan ve üst üste hedef tutturulan gün serisi."""
  goal = daily_goal()
  today = datetime.now(TZ).date()
  today_iso = today.isoformat()
  per_day, pending = {}, 0
  for l in rows("reading_log"):
    day = (l.get("read_at") or "")[:10]
    if is_pending(l):
      if day == today_iso:
        pending += 1
    else:
      per_day[day] = per_day.get(day, 0) + 1
  done = per_day.get(today_iso, 0)
  # Seri: bugün tamamsa bugünden, değilse dünden geriye hedefi tutturan günler
  streak = 0
  d = today if done >= goal else today - timedelta(days=1)
  while per_day.get(d.isoformat(), 0) >= goal:
    streak += 1
    d -= timedelta(days=1)
  return {
      "goal": goal,
      "done": done,
      "pending": pending,
      "remaining": max(goal - done - pending, 0),
      "streak": streak,
      "today_iso": today_iso,
  }


def get_pool_df():
  df = get_books_df()
  df = df[df["is_school"] == 0]  # V0.9 CHANGE: okul kitapları öneri havuzunda yok
  df = df[df["is_outgrown"] == 0]  # V1.0 CHANGE: yaşı geçen kitaplar asla önerilmez
  if datetime.now(TZ).hour >= 19:
    df = df[df["category"] != "Aktivite"]
  return df


# V0.9 CHANGE: öneri havuzu = henüz hiç okunmamış (ve onay beklemeyen) kitaplar.
# Okunmamış kitap kalmadıysa (veya kategoride kalmadıysa) tüm havuza düşer.
def get_unread_pool(cat=None):
  df = get_pool_df()
  if cat and cat != "Tümü":
    df = df[df["category"] == cat]
  pending_ids = {l["book_id"] for l in rows("reading_log") if is_pending(l)}
  unread = df[(df["read_count"] == 0) & (~df["id"].isin(pending_ids))]
  return unread if len(unread) > 0 else df


# V0.9 CHANGE: ekranda zaten gösterilen kitapları tekrar önermemeye çalışır
def sample_books(pool, n):
  shown = {b["id"] for b in st.session_state.current_featured_books}
  fresh = pool[~pool["id"].isin(shown)]
  src = fresh if len(fresh) >= n else pool
  return src.sample(n=min(n, len(src))).to_dict(orient="records")


def spin_wheel():
  pool = get_unread_pool()
  if len(pool) == 0:
    return
  gs = goal_status()
  # V0.9 CHANGE: çark bugünün kalan hedefi kadar kitap önerir (hedef bittiyse 1 bonus)
  n = gs["remaining"] if gs["remaining"] > 0 else 1
  st.session_state.current_featured_books = sample_books(pool, n)
  st.session_state.featured_note = (
      f"🎡 Çark bugün için {n} kitap seçti!"
      if gs["remaining"] > 0
      else "🎉 Bugünkü hedef tamam! Çark sana 1 bonus kitap seçti."
  )


def random_pick():
  pool = get_unread_pool()
  if len(pool) > 0:
    st.session_state.current_featured_books = sample_books(pool, 4)
    st.session_state.featured_note = ""


def pick_category(cat):
  st.session_state.home_active_category = cat
  pool = get_unread_pool(cat)
  st.session_state.current_featured_books = (
      sample_books(pool, 4) if len(pool) > 0 else []
  )
  st.session_state.featured_note = ""


# --- SOL KENAR ÇUBUĞU ---
with st.sidebar:
  st.markdown(
      '<div class="side-logo"><div class="side-logo-emoji">🏰</div>'
      '<div class="side-logo-title">Atlas\'ın Sihirli Kütüphanesi</div>'
      '<div class="side-logo-sub">Keşfet • Oku • Hayal Et</div></div>'
      '<div class="side-label">NAVIGATION</div>',
      unsafe_allow_html=True,
  )

  menu_items = [
      ("🏠", "Ana Sayfa"),
      ("📖", "Kütüphane"),
      ("🏆", "Okuma Yolculuğu"),
      ("🎖️", "Rozetler"),
      ("⚙️", "Yönetici Paneli"),
  ]

  for icon, label in menu_items:
    if st.button(
        f"{icon}  {label}",
        key=f"nav_btn_{label}",
        use_container_width=True,
    ):
      st.session_state.nav_page = label
      st.rerun()

  st.markdown('<div class="side-label">OKUMA DURUMUM</div>', unsafe_allow_html=True)

  total_books = len(home_df)  # V0.9 CHANGE: sadece ev kütüphanesi (okul kitapları iade edilir)
  all_logs = rows("reading_log")
  pending_logs = [l for l in all_logs if is_pending(l)]  # V0.9 CHANGE
  logs_data = approved_logs(all_logs)  # istatistikler yalnızca onaylı okumaları sayar

  now_dt = datetime.now(TZ)
  current_month = now_dt.month
  current_year = now_dt.year

  turkce_aylar = {
      1: "Ocak",
      2: "Şubat",
      3: "Mart",
      4: "Nisan",
      5: "Mayıs",
      6: "Haziran",
      7: "Temmuz",
      8: "Ağustos",
      9: "Eylül",
      10: "Ekim",
      11: "Kasım",
      12: "Aralık",
  }
  current_month_name = turkce_aylar.get(current_month, "")

  month_read_count = 0
  year_read_count = 0

  for l in logs_data:
    rat = l.get("read_at")
    if rat:
      try:
        dt_val = datetime.fromisoformat(rat)
        if dt_val.year == current_year:
          year_read_count += 1
          if dt_val.month == current_month:
            month_read_count += 1
      except Exception:
        pass

  st.markdown(
      "".join([
          f'<div class="side-card"><span>📚 Toplam Kitap</span><b>{total_books}</b></div>',
          f'<div class="side-card"><span>🔥 Bu Ay ({current_month_name})</span><b>{month_read_count}</b></div>',
          f'<div class="side-card"><span>⭐ Bu Yıl ({current_year})</span><b>{year_read_count}</b></div>',
          '<div class="side-ver">Atlas v1.0</div>',
      ]),
      unsafe_allow_html=True,
  )


# --- DETAY MODALI VE GEÇMİŞ OKUMA EKLEME ---
@st.dialog("📖 Kitap Detayları ve Okuma İşlemleri", width="large")
def show_book_detail(b_id):
  fresh_df = get_books_df()
  b_row = fresh_df[fresh_df["id"] == b_id]
  if len(b_row) == 0:
    st.error("Kitap bulunamadı.")
    return

  b = b_row.iloc[0]
  c_img = cover(b.get("cover_url"))

  logs_list = rows("reading_log")
  all_book_logs = [l for l in logs_list if l.get("book_id") == b_id]
  book_logs = approved_logs(all_book_logs)  # V0.9 CHANGE: son okuma yalnızca onaylılardan
  # V0.9 CHANGE: bu kitap için onay bekleyen kayıt var mı / bugün zaten okundu mu
  today_iso = datetime.now(TZ).date().isoformat()
  has_pending = any(is_pending(l) for l in all_book_logs)
  read_today = any((l.get("read_at") or "")[:10] == today_iso for l in book_logs)
  last_read_time = "Henüz okunmadı"
  if book_logs:
    sorted_logs = sorted(
        book_logs, key=lambda x: x.get("read_at") or "", reverse=True
    )
    rat = sorted_logs[0].get("read_at")
    if rat:
      last_read_time = rat[:19].replace("T", " ")

  col_d1, col_d2 = st.columns([1, 2])
  with col_d1:
    if c_img:
      st.image(c_img, use_container_width=True)
    else:
      st.markdown(
          '<div style="font-size: 6rem; text-align: center;">🏫</div>'
          if int(b.get("is_school", 0)) == 1
          else '<div style="font-size: 6rem; text-align: center;">📘</div>',
          unsafe_allow_html=True,
      )
  with col_d2:
    st.markdown(f"### {b['title']}")
    st.markdown(f"✍️ **Yazar:** {b.get('author', 'Bilinmiyor')}")
    st.markdown(f"🏢 **Yayınevi:** {b.get('publisher', 'Bilinmiyor')}")
    st.markdown(f"📌 **ISBN Numarası:** {b.get('isbn', 'Bulunmuyor')}")
    # V0.9 CHANGE: sayfa bilgisi yoksa satırı gösterme
    if pd.notna(b.get("pages")):
      st.markdown(f"📄 **Sayfa Sayısı:** {int(b['pages'])}")
    st.markdown(
        f"📂 **Kategori:** {b.get('category', '-')} &nbsp;|&nbsp; 🎯 **Yaş:**"
        f" {b.get('age', '-')}"
    )
    st.markdown(f"🌍 **Kitap Dili:** {b.get('language', 'Türkçe')}")
    st.markdown(f"🔄 **Toplam Okunma Sayısı:** {int(b.get('read_count', 0))}")
    st.markdown(f"⏱️ **En Son Okunma Tarihi:** {last_read_time}")

  st.markdown("---")
  # V0.9 CHANGE: çocuk "Okudum" der -> kayıt 'pending' olur, ebeveyn onaylayınca sayılır.
  # Aynı kitap günde en fazla 1 kez işaretlenebilir (üst üste basma oyunu biter).
  if has_pending:
    st.info("⏳ Okuman kaydedildi! Annen ya da baban onaylayınca XP kazanacaksın.")
  elif read_today:
    st.success("✅ Bu kitabı bugün zaten okudun. Yarın tekrar okuyabilirsin!")
  else:
    if st.button(
        "✅ Okudum! 🎉",
        key=f"mark_read_{b_id}",
        type="primary",
        use_container_width=True,
    ):
      con = sqlite3.connect(DB_NAME)
      dup = con.execute(
          "SELECT 1 FROM reading_log WHERE book_id = ? AND (status = 'pending'"
          " OR substr(read_at, 1, 10) = ?)",
          (b_id, today_iso),
      ).fetchone()
      if not dup:
        con.execute(
            "INSERT INTO reading_log (book_id, status, read_at, cycle) VALUES"
            " (?, 'pending', ?, 1)",
            (b_id, datetime.now(TZ).replace(tzinfo=None).isoformat(timespec="seconds")),
        )
        con.commit()
      con.close()
      st.toast("Harika! Onay bekliyor ⏳", icon="🎉")
      st.rerun()

  # V0.9 CHANGE: geçmiş tarihli kayıt yalnızca yönetici oturumunda görünür, doğrudan onaylı yazılır
  if st.session_state.admin_logged_in:
    with st.expander("🔐 Yönetici: geçmiş tarihli okuma ekle"):
      with st.form(f"manual_read_form_{b_id}"):
        selected_date = st.date_input(
            "Okunan Tarih Seçin", value=datetime.now(TZ).date()
        )
        selected_time = st.time_input(
            "Okunan Saat Seçin", value=datetime.now(TZ).time()
        )
        if st.form_submit_button(
            "📝 Bu Tarihle Okundu Olarak Kaydet", use_container_width=True
        ):
          combined_dt = datetime.combine(selected_date, selected_time).isoformat()
          con = sqlite3.connect(DB_NAME)
          con.execute(
              "UPDATE books SET read_count = read_count + 1 WHERE id = ?", (b_id,)
          )
          con.execute(
              "INSERT INTO reading_log (book_id, status, read_at, cycle) VALUES"
              " (?, 'read', ?, 1)",
              (b_id, combined_dt),
          )
          con.commit()
          con.close()
          st.toast(f"'{b['title']}' {selected_date} tarihiyle kaydedildi! 🎉", icon="✅")
          st.rerun()

  if st.button("Kapat", use_container_width=True):
    st.rerun()


# Ortak Kitap Kartı
def book_card(b, prefix, cover_h=170):
  rc = int(b.get("read_count", 0) or 0)
  img = cover(b.get("cover_url"))
  is_sch = int(b.get("is_school", 0)) == 1

  cover_html = (
      f'<img src="{html.escape(img)}">'
      if img
      else (
          '<span style="font-size:4rem">🏫</span>'
          if is_sch
          else '<span style="font-size:4rem">📘</span>'
      )
  )

  badge = "⭐ Çok Sevildi" if rc >= 3 else ("🏷️ Yeni" if rc == 0 else "")
  badge_html = f'<div class="book-badge">{badge}</div>' if badge else ""
  school_badge_html = (
      '<div class="school-badge">🏫 Okul Kitabı</div>' if is_sch else ""
  )
  # V1.0 CHANGE: yaşı geçen kitapların etiketi
  if int(b.get("is_outgrown", 0) or 0) == 1:
    badge_html = '<div class="book-badge">🎒 Yaşı Geçti</div>'

  # V0.9 CHANGE: sayfa bilgisi yoksa satır hiç gösterilmez
  try:
    pages_num = float(b.get("pages"))
    pages_line = "" if pd.isna(pages_num) else f"<br>📄 {int(pages_num)} Sayfa"
  except (TypeError, ValueError):
    pages_line = ""

  st.markdown(
      "".join([
          f'<div class="book-card" style="height:{cover_h + 150}px">{badge_html}{school_badge_html}',
          f'<div class="book-cover" style="height:{cover_h}px">{cover_html}</div>',
          f'<div class="book-title">{html.escape(str(b["title"]))}</div>',
          f'<div class="book-meta">👶 {html.escape(str(b.get("age", "-")))}'
          f'{pages_line}<br>🔄 {rc} Kez Okundu</div></div>',
      ]),
      unsafe_allow_html=True,
  )
  if st.button("📖 Hemen Oku", key=f"{prefix}_{b['id']}", use_container_width=True):
    show_book_detail(b["id"])


# --- SAYFA YÖNETİMİ ---
active_page = st.session_state.nav_page

# 1. ANA SAYFA
if active_page == "Ana Sayfa":
  active_cat_label = st.session_state.home_active_category

  # V0.9 CHANGE: günlük hedef göstergesi (✅ onaylı, ⏳ onay bekliyor, boş yuva) ve seri
  gs = goal_status()
  slots = "".join(
      '<div class="goal-slot done">✅</div>'
      if i < gs["done"]
      else (
          '<div class="goal-slot wait">⏳</div>'
          if i < gs["done"] + gs["pending"]
          else '<div class="goal-slot"></div>'
      )
      for i in range(gs["goal"])
  )
  if gs["done"] >= gs["goal"]:
    goal_msg = "🎉 Bugünkü görevi tamamladın!"
    if gs["done"] > gs["goal"]:
      goal_msg += f" (+{gs['done'] - gs['goal']} bonus)"
  elif gs["pending"] > 0:
    goal_msg = "⏳ Onay bekleniyor, annen ya da baban onaylayınca yuva dolar."
  else:
    goal_msg = f"Bugün {gs['remaining']} kitap daha oku!"
  streak_html = (
      f'<span class="goal-streak">🔥 {gs["streak"]} gün üst üste</span>'
      if gs["streak"] > 0
      else ""
  )

  with st.container(key="hero_box"):
    st.markdown(
        "".join([
            '<div class="hero-top"><div class="hero-left">',
            '<div class="hero-title">👋 Merhaba Atlas</div>',
            f'<div class="hero-goalline"><span>🎯</span><div class="goal-slots">{slots}</div>',
            f'<b>{min(gs["done"], gs["goal"])}/{gs["goal"]}</b>{streak_html}</div>',
            f'<div class="goal-msg">{goal_msg}</div></div>',
            f'<div class="hero-right"><b>⭐ Seviye {lvl["level"]}</b>{level_bar_html(lvl)}</div></div>',
        ]),
        unsafe_allow_html=True,
    )
    # V0.9 CHANGE: hedef tamamlanınca günde bir kez balon kutlaması
    if gs["done"] >= gs["goal"] and st.session_state.goal_celebrated != gs["today_iso"]:
      st.session_state.goal_celebrated = gs["today_iso"]
      st.balloons()
    hb1, hb2, _sp = st.columns([1, 1, 3])
    hb1.button("🎡 Sihirli Çark", key="hero_wheel", on_click=spin_wheel, use_container_width=True)
    hb2.button("📚 Rastgele Öner", key="hero_random", on_click=random_pick, use_container_width=True)

  st.caption("🌙 Saat 19:00’dan sonra uyku öncesi huzur için Aktivite haricindeki tüm kitaplar seçilir.")

  st.markdown("#### ✨ Keşfetmek İstediğin Dünyayı Seç")
  categories = [
      ("🌟", "Tümü", "Tümü"), ("🐉", "Hikaye", "Hikaye"),
      ("🚀", "Bilgi", "Bilgi & Keşif"),
      ("💡", "İlk Okuma", "İlk Okuma"), ("🌍", "Doğa", "Doğa & Hayvanlar"),
      ("🔬", "Bilim", "Bilim"), ("💛", "Değerler", "Değerler"),
  ]
  cat_counts = eligible_df["category"].value_counts().to_dict()  # V0.9 CHANGE: okul kitapları sayılmaz
  cat_cols = st.columns(len(categories))
  for idx, (icon, label, actual) in enumerate(categories):
    n = len(eligible_df) if actual == "Tümü" else cat_counts.get(actual, 0)
    is_on = active_cat_label == actual
    cat_cols[idx].button(
        f"{icon} **{label}**\n\n({n})",
        key=f"{'catON' if is_on else 'cat'}_{idx}",
        on_click=pick_category,
        args=(actual,),
        use_container_width=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)
  st.markdown(
      "#### ⭐ Senin İçin Seçtiklerimiz"
      + (f" ({active_cat_label})" if active_cat_label != "Tümü" else "")
  )

  if st.session_state.featured_note:
    st.caption(st.session_state.featured_note)

  featured_books = st.session_state.current_featured_books
  if not featured_books or len(featured_books) == 0:
    # V0.9 CHANGE: ilk açılışta da önce okunmamış kitaplar, günlük hedef kadar
    default_pool = get_unread_pool(active_cat_label)
    if len(default_pool) > 0:
      featured_books = sample_books(default_pool, min(gs["goal"], len(default_pool)))
    st.session_state.current_featured_books = featured_books

  if featured_books:
    home_cols = st.columns(4)
    for idx, book in enumerate(featured_books[:4]):
      with home_cols[idx]:
        live = books_df[books_df["id"] == book["id"]]
        book_card(live.iloc[0] if len(live) else book, "home", 170)

  st.markdown("#### 📖 Son Maceraların")
  title_map = dict(zip(books_df["id"], books_df["title"]))
  school_ids = set(books_df.loc[books_df["is_school"] == 1, "id"])  # V0.9 CHANGE
  recent, seen = [], set()
  for l in sorted(logs_data, key=lambda x: x.get("read_at") or "", reverse=True):
    bid = l.get("book_id")
    if bid in title_map and bid not in seen:
      seen.add(bid)
      recent.append((title_map[bid], (l.get("read_at") or "")[:10], bid in school_ids))
    if len(recent) == 5:
      break
  if recent:
    st.markdown(
        "".join(
            f'<div class="recent-item"><div>{"🏫" if sch else "📖"} <b>{html.escape(str(t))}</b></div><span>{d}</span></div>'
            for t, d, sch in recent
        ),
        unsafe_allow_html=True,
    )
  else:
    st.info("Henüz okunan kitap yok. İlk maceranı başlat! 🚀")


# 2. KÜTÜPHANE
elif active_page == "Kütüphane":
  st.markdown("### 📖 Kütüphane Arşivi")

  # V0.9 CHANGE: okul kitapları kütüphanede durmaz, sadece ev kitapları listelenir
  lib_base_df = home_df

  all_publishers = sorted(
      {
          str(p).strip()
          for p in lib_base_df["publisher"].dropna()
          if str(p).strip() != ""
      }
  )

  col_s1, col_s2, col_s3, col_s4 = st.columns([2, 1, 1, 1])
  with col_s1:
    search_query = st.text_input(
        "Kitap veya Yazar Ara",
        placeholder="Kelime yazın...",
        key="lib_search",
    )
  with col_s2:
    pub_filter = st.selectbox(
        "Yayınevi Filtrele", ["Tümü"] + all_publishers, key="lib_pub_select"
    )
  with col_s3:
    cat_options = ["Tümü"] + CATEGORIES  # V1.0 CHANGE
    default_cat_idx = (
        cat_options.index(st.session_state.selected_category)
        if st.session_state.selected_category in cat_options
        else 0
    )
    cat_filter = st.selectbox(
        "Kategori Filtrele", cat_options, index=default_cat_idx, key="lib_cat"
    )
  with col_s4:
    # V1.0 CHANGE: yaşı geçen kitaplar için filtre
    age_filter = st.selectbox(
        "Yaş Uygunluğu", ["Uygun olanlar", "Tümü", "Yaşı geçenler"], key="lib_age"
    )

  filtered_lib = lib_base_df.copy()
  if pub_filter != "Tümü":
    filtered_lib = filtered_lib[filtered_lib["publisher"] == pub_filter]
  if search_query:
    q = search_query.strip()
    filtered_lib = filtered_lib[
        filtered_lib["title"]
        .astype(str)
        .str.contains(q, case=False, na=False)
        | filtered_lib["author"]
        .astype(str)
        .str.contains(q, case=False, na=False)
    ]
  if cat_filter != "Tümü":
    filtered_lib = filtered_lib[filtered_lib["category"] == cat_filter]
  if age_filter == "Uygun olanlar":
    filtered_lib = filtered_lib[filtered_lib["is_outgrown"] == 0]
  elif age_filter == "Yaşı geçenler":
    filtered_lib = filtered_lib[filtered_lib["is_outgrown"] == 1]

  filtered_lib = filtered_lib.sort_values(by="title", ascending=True)
  st.write(f"📚 Toplam **{len(filtered_lib)}** kitap listeleniyor.")

  for start in range(0, len(filtered_lib), 4):
    cols = st.columns(4)
    for c_idx, (_, b) in enumerate(filtered_lib.iloc[start : start + 4].iterrows()):
      with cols[c_idx]:
        book_card(b, "lib", 210)


# 3. OKUMA YOLCULUĞU
elif active_page == "Okuma Yolculuğu":
  st.markdown("### 🏆 Okuma Karnesi ve Detaylı İstatistikler")

  milestones = [
      ("🏠 Ev", 0), ("✈ Havalimanı", 5), ("🚂 Tren İstasyonu", 10),
      ("🏰 Şato", 20), ("🌳 Doğa", 35), ("🚀 Uzay", 50), ("🪐 Galaksi", 75),
  ]
  cur_idx = max(i for i, (_, req) in enumerate(milestones) if total_read_books >= req)
  stops = []
  for i, (label, req) in enumerate(milestones):
    state = "done" if i < cur_idx else ("now" if i == cur_idx else "lock")
    icon, name = label.split(" ", 1)
    sub = {"done": "✅ Tamamlandı", "now": "📍 Buradasın", "lock": f"🔒 {req} kitap"}[state]
    stops.append(
        f'<div class="stop {state}"><div class="stop-icon">{icon}</div>{name}<small>{sub}</small></div>'
    )
  st.markdown(f'<div class="journey">{"".join(stops)}</div>', unsafe_allow_html=True)
  if cur_idx < len(milestones) - 1:
    nxt_label, nxt_req = milestones[cur_idx + 1]
    prev_req = milestones[cur_idx][1]
    st.progress(
        min((total_read_books - prev_req) / (nxt_req - prev_req), 1.0),
        text=f"{nxt_label} durağına {nxt_req - total_read_books} kitap kaldı",
    )
  else:
    st.success("🪐 Tüm durakları tamamladın!")
  st.markdown("---")

  # V0.9 CHANGE: okul kitapları da "okunan"a dahil; yüzde sadece ev kütüphanesine göre
  total_books_count = len(home_df)
  read_books_df = books_df[books_df["read_count"] > 0]
  total_read_count = len(read_books_df)
  home_read_count = int((home_df["read_count"] > 0).sum())
  school_read_count = total_read_count - home_read_count

  # V0.9 CHANGE: sayfa bilgisi olmayan kitaplar toplama katılmaz (varsayılan yok)
  total_pages_read = int(
      (read_books_df["pages"].fillna(0) * read_books_df["read_count"]).sum()
  )

  col_m1, col_m2, col_m3 = st.columns(3)
  with col_m1:
    st.metric(
        label="Toplam Okunan Kitap",
        value=f"{total_read_count}",
    )
    st.caption(f"🏡 {home_read_count} ev · 🏫 {school_read_count} okul")
    home_pct = home_read_count / max(total_books_count, 1)
    st.progress(home_pct, text=f"Ev kütüphanesi %{round(home_pct * 100, 1)}")
  with col_m2:
    st.metric(label="Toplam Okunan Sayfa", value=f"{total_pages_read} Sayfa 📄")
  with col_m3:
    stories = home_df[home_df["category"] == "Hikaye"]
    story_done = len(stories[stories["read_count"] > 0])
    st.metric(
        label="Tamamlanan Hikâyeler", value=f"{story_done} / {len(stories)}"
    )
    st.progress(
        story_done / max(len(stories), 1),
        text=f"%{round((story_done / max(len(stories), 1)) * 100, 1)}",
    )

  # V0.9 CHANGE: Türkçe / Dutch okuma özeti
  st.markdown("---")
  st.markdown("#### 🌍 Hangi Dilde Okudum?")
  lang_sum = language_read_summary(logs_data, books_df)
  lang_cols = st.columns(3 if "Diğer" in lang_sum else 2)
  lang_cols[0].markdown(lang_card_html("🇹🇷 Türkçe", lang_sum.get("Türkçe")), unsafe_allow_html=True)
  lang_cols[1].markdown(lang_card_html("🇳🇱 Dutch", lang_sum.get("Dutch")), unsafe_allow_html=True)
  if "Diğer" in lang_sum:
    lang_cols[2].markdown(lang_card_html("🌍 Diğer", lang_sum["Diğer"]), unsafe_allow_html=True)
  st.caption("Her okuma kaydı bir kez sayılır (aynı kitabı tekrar okumak da dahil).")

  st.markdown("---")
  st.markdown("#### 📊 Kategoriye Göre Okuma Dağılımı")

  cat_groups = (
      home_df.groupby("category")
      .agg(Toplam=("id", "count"), Okunan=("read_count", lambda x: (x > 0).sum()))
      .reset_index()
  )

  cat_cols = st.columns(len(cat_groups) if len(cat_groups) > 0 else 1)
  for idx, row in cat_groups.iterrows():
    c_name = row["category"]
    c_tot = row["Toplam"]
    c_done = row["Okunan"]
    c_perc = c_done / c_tot if c_tot > 0 else 0

    with cat_cols[idx % len(cat_cols)]:
      st.markdown(
          f"""
            <div class="cat-box">
                <h4 style="color: #4f46e5; margin-bottom: 5px; font-weight: 800;">📂 {c_name}</h4>
                <p style="font-size: 0.9rem; color: #64748b; margin-bottom: 10px;">Okunan: <b>{c_done}</b> / Toplam: <b>{c_tot}</b></p>
                <div style="background: #e2e8f0; border-radius: 99px; height: 10px; width: 100%; overflow: hidden;">
                    <div style="background: #6366f1; height: 100%; width: {c_perc * 100}%;"></div>
                </div>
                <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 5px;">%{round(c_perc * 100, 1)} Tamamlandı</p>
            </div>
            """,
          unsafe_allow_html=True,
      )


# 4. ROZETLER
elif active_page == "Rozetler":
  st.markdown("### 🎖️ Atlas'ın Başarı Rozetleri")
  st.markdown(
      "Okuduğun kitap sayısına göre kazandığın sihirli rozetler burada"
      " listelenir!"
  )

  tot_read = len(books_df[books_df["read_count"] > 0])

  c1, c2, c3 = st.columns(3)
  c1.markdown(f'<div class="stat-card"><small>LEVEL</small><div class="stat-val">⭐ {lvl["level"]}</div></div>', unsafe_allow_html=True)
  c2.markdown(f'<div class="stat-card"><small>XP</small><div class="stat-val">{lvl["xp"]}</div></div>', unsafe_allow_html=True)
  c3.markdown(f'<div class="stat-card"><small>İLERLEME</small>{level_bar_html(lvl)}</div>', unsafe_allow_html=True)

  r_cols = st.columns(3)
  badges = [
      ("🥉", "İlk Adım", "İlk kitabını okudun!", 1),
      ("🥈", "Kitap Kurdu", "5 kitap okumayı başardın!", 5),
      ("🥇", "Macera Uzmanı", "10 kitap okudun!", 10),
      ("👑", "Kütüphane Kralı", "25 kitap okudun!", 25),
      ("🌟", "Sihirli Kaşif", "50 kitaba ulaştın!", 50),
      ("🏰", "Efsane Okur", "Tüm kütüphaneyi fethettin!", 100),
  ]

  for idx, (icon, title, desc, req) in enumerate(badges):
    with r_cols[idx % 3]:
      unlocked = tot_read >= req
      bg = "#f0fdf4" if unlocked else "#f8fafc"
      border_c = "#bbf7d0" if unlocked else "#e2e8f0"
      status_txt = "✅ KAZANILDI!" if unlocked else f"🔒 {req} Kitap Gerekli"

      st.markdown(
          f"""
            <div style="background: {bg}; border: 1px solid {border_c}; border-radius: 20px; padding: 20px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
                <div style="font-size: 3.5rem; margin-bottom: 5px;">{icon}</div>
                <h4 style="color: #1e293b; margin: 5px 0; font-weight: 800;">{title}</h4>
                <p style="color: #64748b; font-size: 0.85rem; margin-bottom: 10px;">{desc}</p>
                <b style="font-size: 0.85rem; color: {'#15803d' if unlocked else '#94a3b8'};">{status_txt}</b>
            </div>
        """,
          unsafe_allow_html=True,
      )


# 5. YÖNETİCİ PANELİ
elif active_page == "Yönetici Paneli":
  st.markdown(ADMIN_CSS, unsafe_allow_html=True)
  st.markdown(
      '<div class="admin-head"><h2>Yönetim Paneli</h2>'
      '<p>Katalog, kapak ve okuma kayıtları yönetimi</p></div>',
      unsafe_allow_html=True,
  )

  if not st.session_state.admin_logged_in:
    try:
      expected_pin = (
          st.secrets.get("ADMIN_PIN", "1234")
          if hasattr(st, "secrets")
          else "1234"
      )
    except Exception:
      expected_pin = "1234"

    entered_pin = st.text_input(
        "Yönetici Giriş PIN Kodu", type="password", key="admin_pin_input"
    )
    if entered_pin == expected_pin:
      st.session_state.admin_logged_in = True
      st.success("Giriş başarılı! Yönetici paneli aktif.")
      st.rerun()
    elif entered_pin:
      st.error("PIN kodu hatalı!")
  else:
    st.success("🔐 Yönetici Oturumu Açık")
    if st.button("Çıkış Yap"):
      st.session_state.admin_logged_in = False
      st.rerun()

    missing_n = int((books_df["cover_url"].isna() | (books_df["cover_url"] == "")).sum())
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Toplam Kitap", total_books)
    k2.metric("Okuma Kaydı", len(logs_data))
    k3.metric("Bu Ay", month_read_count)
    k4.metric("Onay Bekleyen", len(pending_logs))  # V0.9 CHANGE
    k5.metric("Kapağı Eksik", missing_n)

    # V0.9 CHANGE: günlük hedef ayarı
    with st.expander("🎯 Günlük hedef ayarı"):
      goal_input = st.number_input(
          "Günde kaç kitap?",
          min_value=1,
          max_value=10,
          value=daily_goal(),
          step=1,
          key="goal_input",
      )
      if st.button("Hedefi Kaydet", key="save_goal"):
        set_setting("daily_goal", int(goal_input))
        st.toast(f"Günlük hedef {int(goal_input)} kitap olarak kaydedildi.", icon="🎯")
        st.rerun()

    st.markdown("---")

    (
        adm_tab_pending,
        adm_tab_school,
        adm_tab1,
        adm_tab2,
        adm_tab3,
        adm_missing_covers,
        adm_tab4,
        adm_tab5,
        adm_tab6,
        adm_tab7,
        adm_tab8,
        adm_tab_delete,
        adm_tab_outgrown,
        adm_tab_catreview,
    ) = st.tabs([
        f"⏳ Onay Bekleyenler ({len(pending_logs)})",  # V0.9 CHANGE
        "🏫 Okul Kitabı Ekle",
        "➕ Yeni Kitap",
        "✏️ Düzenle",
        "🎨 Kapaklar",
        "🖼️ Eksik Görseller",
        "↩ Geri Al",
        "📊 Özet",
        "📝 Loglar",
        "🧹 Sıfırla",
        "💾 DB Yedek",
        "🗑️ Kitap Sil",
        "🎒 Yaşı Geçti",
        "🔎 Kategori İncelemesi",
    ])

    # V0.9 CHANGE: çocuğun "Okudum" dediği kayıtlar burada onaylanır / reddedilir
    with adm_tab_pending:
      st.subheader("⏳ Onay Bekleyen Okumalar")
      if not pending_logs:
        st.success("Bekleyen okuma yok 🎉")
      else:
        if st.button("✅ Hepsini Onayla", key="approve_all", use_container_width=True):
          for pl in pending_logs:
            approve_reading(pl["id"])
          st.toast(f"{len(pending_logs)} okuma onaylandı.", icon="✅")
          st.rerun()
        pend_titles = dict(zip(books_df["id"], books_df["title"]))
        for pl in sorted(pending_logs, key=lambda x: x.get("read_at") or ""):
          pc1, pc2, pc3 = st.columns([5, 1.3, 1.3])
          pc1.write(
              f"📖 **{pend_titles.get(pl['book_id'], '(silinmiş kitap)')}** —"
              f" {(pl.get('read_at') or '')[:16].replace('T', ' ')}"
          )
          if pc2.button("✅ Onayla", key=f"approve_{pl['id']}"):
            approve_reading(pl["id"])
            st.rerun()
          if pc3.button("✖ Reddet", key=f"reject_{pl['id']}"):
            reject_reading(pl["id"])
            st.rerun()

    with adm_tab_school:
      st.subheader("🏫 De Vuurvlinder Okul Kitabı Ekle")
      st.markdown("İstersen **ISBN Numarası** girerek detayları otomatik buldurabilir, istersen sadece **Kitap Adı** yazarak ekleyebilirsin.")
      # V0.9 CHANGE: okul kitabı kütüphanede durmaz; eklenince okunmuş (Dutch) olarak sayılır
      st.caption("Okul kitapları kütüphanede listelenmez. Eklediğin an Dutch olarak okunmuş sayılır (aylık/yıllık istatistik, XP ve rozetler).")

      with st.form("admin_school_quick_form"):
        sch_isbn = st.text_input("ISBN Numarası (Otomatik bulma için)", placeholder="Örn: 97890258... (İsteğe bağlı)")
        quick_title = st.text_input("Kitap Adı (ISBN boşsa zorunlu)", placeholder="Örn: Nijntje op school")
        # V0.9 CHANGE: sayfa sayısı varsayılan değersiz, boş bırakılabilir
        quick_pages = st.number_input(
            "Sayfa Sayısı (biliniyorsa)",
            min_value=1,
            max_value=500,
            value=None,
            step=1,
            placeholder="Boş bırakılabilir",
        )
        sch_date = st.date_input("Okunduğu Tarih", value=datetime.now(TZ).date())
        sch_time = st.time_input("Okunduğu Saat", value=datetime.now(TZ).time())

        if st.form_submit_button("Okul Kitabını Ekle"):
          final_title = quick_title.strip()
          final_author = "De Vuurvlinder Okulu"
          final_publisher = "De Vuurvlinder"
          final_pages = quick_pages
          final_cover = ""
          final_isbn = sch_isbn

          # ISBN girildiyse API'den çekmeye çalış
          if sch_isbn.strip():
            with st.spinner("ISBN ile kitap bilgileri aranıyor... 🔍"):
              book_data = fetch_book_by_isbn(sch_isbn)
              if book_data:
                final_title = book_data["title"] or quick_title
                final_author = book_data["author"]
                final_publisher = book_data["publisher"]
                final_pages = book_data["pages"]
                final_cover = book_data["cover_url"]
                final_isbn = book_data["isbn"]
                st.success("Kitap bilgileri başarıyla bulundu! ✨")
              else:
                st.warning("ISBN ile eşleşen kitap bulunamadı, girdiğiniz isimle kaydediliyor.")

          if final_title:
            read_iso = datetime.combine(sch_date, sch_time).isoformat()
            con = sqlite3.connect(DB_NAME)
            # V0.9 CHANGE: aynı okul kitabı daha önce eklendiyse yeni kitap açma, okuma sayısını artır
            existing = con.execute(
                "SELECT id FROM books WHERE is_school = 1 AND lower(title) = lower(?)",
                (final_title,),
            ).fetchone()
            if existing:
              bid = existing[0]
              con.execute(
                  "UPDATE books SET read_count = read_count + 1 WHERE id = ?", (bid,)
              )
            else:
              bid = "SCH-" + uuid.uuid4().hex[:8].upper()
              con.execute(
                  "INSERT INTO books (id, title, author, publisher, isbn, category, pages, cover_url, language, read_count, created_at, is_school) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Dutch', 1, ?, 1)",
                  (
                      bid,
                      final_title,
                      final_author,
                      final_publisher,
                      final_isbn,
                      "Hikaye",
                      int(final_pages) if final_pages else None,
                      final_cover,
                      datetime.now(TZ).isoformat(),
                  ),
              )
            # V0.9 CHANGE: okuma kaydı da hemen oluşturulur -> aylık/yıllık sayıma girer
            con.execute(
                "INSERT INTO reading_log (book_id, status, read_at, cycle) VALUES (?, 'read', ?, 1)",
                (bid, read_iso),
            )
            con.commit()
            con.close()
            st.toast(f"'{final_title}' okunmuş olarak kaydedildi! 🎒", icon="✅")
            st.rerun()
          else:
            st.error("Lütfen en azından kitap adını girin.")

    with adm_tab1:
      with st.form("admin_add_form"):
        st.subheader("Yeni Kitap Ekle")
        new_t = st.text_input("Kitap Adı")
        new_a = st.text_input("Yazar")
        new_p = st.text_input("Yayınevi")
        new_isbn = st.text_input("ISBN Numarası")
        new_c = st.selectbox("Kategori", CATEGORIES)  # V1.0 CHANGE
        new_ag = st.text_input("Yaş Grubu", "5+")
        # V0.9 CHANGE: varsayılan sayfa sayısı kaldırıldı, boş bırakılabilir
        new_pg = st.number_input(
            "Sayfa Sayısı", min_value=1, value=None, step=1, placeholder="Boş bırakılabilir"
        )
        new_lang = st.text_input("Kitap Dili", "Türkçe")
        new_cv = st.text_input("Kapak Görsel URL")

        if st.form_submit_button("Kütüphaneye Kaydet"):
          if new_t:
            bid = "MAN-" + uuid.uuid4().hex[:8].upper()
            con = sqlite3.connect(DB_NAME)
            con.execute(
                "INSERT INTO books (id, title, author, publisher, isbn, category, age, pages, language, cover_url, read_count, created_at, is_school) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 0)",
                (
                    bid,
                    new_t,
                    new_a,
                    new_p,
                    new_isbn,
                    new_c,
                    new_ag,
                    int(new_pg) if new_pg else None,  # V0.9 CHANGE
                    new_lang,
                    new_cv,
                    datetime.now(TZ).isoformat(),
                ),
            )
            con.commit()
            con.close()
            st.success(f"'{new_t}' başarıyla eklendi!")
            st.rerun()

    with adm_tab2:
      st.subheader("✏️ Kitap Künyesini Düzenle")
      edit_search_q = st.text_input(
          "🔍 Düzenlenecek Kitabı Ara",
          placeholder="Kitap adı yazın...",
          key="edit_book_search",
      )
      matched_edit_books = (
          books_df[
              books_df["title"]
              .astype(str)
              .str.contains(edit_search_q.strip(), case=False, na=False)
          ]
          if edit_search_q.strip()
          else pd.DataFrame()
      )

      if len(matched_edit_books) > 0:
        for _, eb in matched_edit_books.iterrows():
          with st.form(f"edit_book_form_{eb['id']}"):
            up_title = st.text_input("Kitap Adı", value=eb["title"])
            up_author = st.text_input(
                "Yazar", value=str(eb.get("author", ""))
            )
            up_pub = st.text_input(
                "Yayınevi", value=str(eb.get("publisher", ""))
            )
            # V0.9 CHANGE: bilgi yoksa 24 yazma, boş göster
            up_pages = st.number_input(
                "Sayfa Sayısı",
                min_value=1,
                step=1,
                value=int(eb["pages"]) if pd.notna(eb.get("pages")) else None,
                placeholder="Bilinmiyor",
                key=f"up_pages_{eb['id']}",
            )
            up_lang = st.text_input(
                "Dil", value=str(eb.get("language", "Türkçe"))
            )
            # V1.0 CHANGE: kategori düzenleme ve "yaşı geçti" işareti
            cur_cat = eb.get("category")
            cat_choices = CATEGORIES if cur_cat in CATEGORIES else [cur_cat] + CATEGORIES
            up_cat = st.selectbox(
                "Kategori", cat_choices,
                index=cat_choices.index(cur_cat) if cur_cat in cat_choices else 0,
                key=f"up_cat_{eb['id']}",
            )
            up_out = st.checkbox(
                "🎒 Yaşı geçti (öneri listelerine hiç girmesin)",
                value=bool(int(eb.get("is_outgrown", 0))),
                key=f"up_out_{eb['id']}",
            )
            if st.form_submit_button("Güncelle"):
              con = sqlite3.connect(DB_NAME)
              con.execute(
                  "UPDATE books SET title = ?, author = ?, publisher = ?, pages = ?, language = ?, category = ?, is_outgrown = ? WHERE id = ?",
                  (up_title, up_author, up_pub, int(up_pages) if up_pages else None, up_lang, up_cat, int(up_out), eb["id"]),
              )
              con.commit()
              con.close()
              st.success("Güncellendi!")
              st.rerun()

    with adm_tab3:
      st.subheader("🎨 Kapak Düzenle")
      cover_search_query = st.text_input(
          "🔍 Kitap Ara", key="cover_search_input"
      )
      filtered_cover_books = (
          books_df[
              books_df["title"]
              .astype(str)
              .str.contains(cover_search_query.strip(), case=False, na=False)
          ]
          if cover_search_query.strip()
          else books_df[
              books_df["cover_url"].isna() | (books_df["cover_url"] == "")
          ]
      )

      for _, b in filtered_cover_books.iterrows():
        with st.form(f"quick_cover_{b['id']}"):
          st.write(f"📖 {b['title']}")
          new_url_val = st.text_input(
              "Kapak URL", value=str(b.get("cover_url", "")), key=f"url_{b['id']}"
          )
          if st.form_submit_button("Kaydet"):
            con = sqlite3.connect(DB_NAME)
            con.execute(
                "UPDATE books SET cover_url = ? WHERE id = ?",
                (new_url_val, b["id"]),
            )
            con.commit()
            con.close()
            st.success("Kapak güncellendi!")
            st.rerun()

    with adm_missing_covers:
      st.subheader("🖼 Görseli Eksik Olan Kitaplar ve Hızlı Kapak Ekleme")
      missing_df = books_df[
          books_df["cover_url"].isna() | (books_df["cover_url"] == "")
      ]
      st.write(f"🖼️ Görseli Olmayan Kitap Sayısı: **{len(missing_df)}**")

      if len(missing_df) > 0:
        for _, mb in missing_df.iterrows():
          with st.form(f"missing_cover_form_{mb['id']}"):
            st.markdown(
                f"📖 **{mb['title']}** — *{mb.get('author', 'Bilinmiyor')}*"
                f" ({mb.get('category', '-')})"
            )
            new_missing_url = st.text_input(
                "Kapak Görsel URL", key=f"missing_url_{mb['id']}"
            )
            if st.form_submit_button("Kapak Ekle"):
              con = sqlite3.connect(DB_NAME)
              con.execute(
                  "UPDATE books SET cover_url = ? WHERE id = ?",
                  (new_missing_url, mb["id"]),
              )
              con.commit()
              con.close()
              st.success(f"'{mb['title']}' için kapak kaydedildi! 🎉")
              st.rerun()
      else:
        st.success(
            "Tebrikler! Kütüphanenizde görseli eksik olan hiç kitap kalmamış!"
            " 🎉"
        )

    with adm_tab4:
      st.subheader("↩ En Son Okumayı Geri Al")
      read_books_df_adm = books_df[books_df["read_count"] > 0]
      for _, rb in read_books_df_adm.iterrows():
        col_rb1, col_rb2 = st.columns([3, 1])
        with col_rb1:
          st.write(
              f"📖 **{rb['title']}** (Okunma: {int(rb['read_count'])})"
          )
        with col_rb2:
          if st.button("Geri Al", key=f"undo_{rb['id']}"):
            con = sqlite3.connect(DB_NAME)
            last_log = con.execute(
                # V0.9 CHANGE: geri al, onay bekleyen kaydı değil onaylı son kaydı siler
                "SELECT id FROM reading_log WHERE book_id = ? AND COALESCE(status, '') != 'pending'"
                " ORDER BY read_at DESC LIMIT 1",
                (rb["id"],),
            ).fetchone()
            if last_log:
              con.execute("DELETE FROM reading_log WHERE id = ?", (last_log[0],))
            con.execute(
                "UPDATE books SET read_count = MAX(0, read_count - 1) WHERE id"
                " = ?",
                (rb["id"],),
            )
            con.commit()
            con.close()
            st.success("Geri alındı!")
            st.rerun()

    with adm_tab5:
      st.subheader("📊 Okuma Geçmişi Özeti")
      logs_list = approved_logs(rows("reading_log"))  # V0.9 CHANGE: sadece onaylı okumalar
      if logs_list:
        summary_map = {}
        for l in logs_list:
          bid = l.get("book_id")
          rat = l.get("read_at", "")
          if bid not in summary_map:
            summary_map[bid] = {"count": 0, "last_read": ""}
          summary_map[bid]["count"] += 1
          if rat > summary_map[bid]["last_read"]:
            summary_map[bid]["last_read"] = rat

        summary_data = []
        book_dict = {b["id"]: b for b in books_df.to_dict("records")}
        for b_id, data in summary_map.items():
          b_info = book_dict.get(b_id, {})
          summary_data.append({
              "Kitap Adı": b_info.get("title", ""),
              "Yazar": b_info.get("author", ""),
              "Toplam Okunma": data["count"],
              "En Son Okunma": data["last_read"][:19].replace("T", " "),
          })
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
      else:
        st.info("Kayıt yok.")

    with adm_tab6:
      st.subheader("📝 Ham Loglar")
      st.dataframe(pd.DataFrame(rows("reading_log")), use_container_width=True)

    with adm_tab7:
      st.subheader("🧹 Sıfırlama")
      if st.button("Tüm Sayaçları Sıfırla"):
        con = sqlite3.connect(DB_NAME)
        con.execute("UPDATE books SET read_count = 0")
        con.execute("DELETE FROM reading_log")
        con.commit()
        con.close()
        st.success("Sıfırlandı!")
        st.rerun()

    with adm_tab8:
      st.subheader("💾 Veritabanı Yedek İndir")
      if os.path.exists(DB_NAME):
        with open(DB_NAME, "rb") as f:
          st.download_button(
              label="📥 atlas_library.db İndir",
              data=f,
              file_name="atlas_library.db",
              mime="application/x-sqlite3",
              use_container_width=True,
          )

      # V0.9 CHANGE: indirilen yedeği geri yükleme
      st.markdown("---")
      st.subheader("♻️ Veritabanını Geri Yükle")
      st.warning(
          "Yüklenen yedek, şu anki tüm verinin (kitaplar ve okuma geçmişi) yerine geçer."
          " İşlemden önce mevcut veritabanının bir kopyası otomatik alınır."
      )
      restore_file = st.file_uploader(
          "Yedek dosyası (atlas_library.db)",
          type=["db", "sqlite", "sqlite3"],
          key="restore_upload",
      )
      if restore_file is not None:
        restore_bytes = restore_file.getvalue()
        new_info, restore_err = inspect_backup(restore_bytes)
        if restore_err:
          st.error(restore_err)
        else:
          cur_info = summarize_db(DB_NAME) or {"books": 0, "logs": 0, "pending": 0}
          rc1, rc2 = st.columns(2)
          rc1.metric(
              "Şu anki veritabanı",
              f"{cur_info['books']} kitap",
              f"{cur_info['logs']} okuma kaydı",
              delta_color="off",
          )
          rc2.metric(
              "Yüklenen yedek",
              f"{new_info['books']} kitap",
              f"{new_info['logs']} okuma kaydı",
              delta_color="off",
          )
          if new_info["logs"] < cur_info["logs"]:
            st.warning(
                f"Dikkat: yüklenen yedekte şu anki veritabanından {cur_info['logs'] - new_info['logs']}"
                " okuma kaydı daha az. Yanlış dosyayı seçmediğinden emin ol."
            )
          restore_ok = st.checkbox(
              "Mevcut veriyi bu yedekle değiştirmeyi onaylıyorum.", key="restore_confirm"
          )
          if st.button(
              "♻️ Geri Yükle",
              key="restore_btn",
              disabled=not restore_ok,
              use_container_width=True,
          ):
            restore_db(restore_bytes)
            st.toast("Veritabanı geri yüklendi.", icon="✅")
            st.rerun()

    # V1.0 CHANGE: yaşı geçen kitapları işaretle (arama + filtre + tıkla-işaretle tablo)
    with adm_tab_outgrown:
      st.subheader("🎒 Yaşı Geçen Kitaplar")
      st.caption(
          "Kitabı bulun, 'Yaşı geçti' kutusunu işaretleyin, Kaydet'e basın. "
          "İşaretli kitaplar öneri listelerine hiç girmez; kütüphanede 🎒 etiketiyle kalır, "
          "geçmiş istatistikler korunur. Sadece tabloda görünen kitaplar değişir."
      )
      og_n = int((home_df["is_outgrown"] == 1).sum())
      st.info(f"Şu an yaşı geçen: **{og_n}** kitap  ·  Öneri havuzu: **{len(eligible_df)}** kitap")

      f1, f2, f3 = st.columns([2, 1, 1])
      og_q = f1.text_input("🔍 Kitap ara", key="og_search", placeholder="Kitap adı...")
      og_age_opts = ["Tümü"] + sorted(
          {str(a) for a in home_df["age"].dropna() if str(a).strip()}
      )
      og_age = f2.selectbox("Yaş grubu", og_age_opts, key="og_age")
      og_view = f3.selectbox(
          "Göster", ["Hepsi", "Sadece işaretliler", "Sadece işaretsizler"], key="og_view"
      )

      og_df = home_df.copy()
      if og_q.strip():
        og_df = og_df[og_df["title"].astype(str).str.contains(og_q.strip(), case=False, na=False)]
      if og_age != "Tümü":
        og_df = og_df[og_df["age"].astype(str) == og_age]
      if og_view == "Sadece işaretliler":
        og_df = og_df[og_df["is_outgrown"] == 1]
      elif og_view == "Sadece işaretsizler":
        og_df = og_df[og_df["is_outgrown"] == 0]
      og_df = og_df.sort_values("title")

      table = pd.DataFrame({
          "ID": og_df["id"].values,
          "Kitap": og_df["title"].values,
          "Yaş": og_df["age"].astype(str).values,
          "Kategori": og_df["category"].values,
          "🎒 Yaşı geçti": og_df["is_outgrown"].astype(bool).values,
      })
      st.write(f"**{len(table)}** kitap gösteriliyor.")
      edited = st.data_editor(
          table,
          hide_index=True,
          use_container_width=True,
          disabled=["ID", "Kitap", "Yaş", "Kategori"],
          column_config={"ID": None},
          key=f"og_editor_{og_q}_{og_age}_{og_view}",
      )
      changed = edited[edited["🎒 Yaşı geçti"] != table["🎒 Yaşı geçti"]]
      if len(changed) > 0:
        st.warning(f"{len(changed)} kitapta değişiklik var; kaydedilmedi.")
      if st.button("💾 Değişiklikleri Kaydet", key="outgrown_save", disabled=len(changed) == 0):
        con = sqlite3.connect(DB_NAME)
        con.executemany(
            "UPDATE books SET is_outgrown = ? WHERE id = ?",
            [(int(r["🎒 Yaşı geçti"]), r["ID"]) for _, r in changed.iterrows()],
        )
        con.commit()
        con.close()
        st.success(f"{len(changed)} kitap güncellendi.")
        st.rerun()

    # V1.0 CHANGE: internet araştırmasına dayalı kategori önerilerini önizle ve onayla
    with adm_tab_catreview:
      st.subheader("🔎 Kategori İncelemesi")
      st.caption(
          "Kitap adları internette araştırılarak hazırlanan yeni kategori önerileri. "
          "Önce önizleyin, sonra isterseniz uygulayın. Uygulamadan önce DB yedeği alınır."
      )
      cur_cats = dict(zip(books_df["id"], books_df["category"]))
      title_of = dict(zip(books_df["id"], books_df["title"]))
      diff_rows = [
          {"ID": k, "Kitap": title_of.get(k, "?"), "Şimdi": cur_cats.get(k),
           "Önerilen": v[0], "Gerekçe": v[1], "Güven": v[2]}
          for k, v in CATEGORY_REVIEW.items()
          if k in cur_cats and cur_cats[k] != v[0]
      ]
      if not diff_rows:
        st.success("✅ Tüm kategoriler inceleme önerileriyle uyumlu.")
      else:
        diff_df = pd.DataFrame(diff_rows)
        st.write(f"**{len(diff_df)}** kitapta değişiklik öneriliyor.")
        only_conf = st.checkbox("Sadece 'yüksek' güvenli önerileri uygula", value=False, key="catrev_hi")
        view = diff_df[diff_df["Güven"] == "yüksek"] if only_conf else diff_df
        st.dataframe(view, use_container_width=True, hide_index=True)
        ok_apply = st.checkbox("Önizlemeyi inceledim, uygulansın", key="catrev_ok")
        if st.button("✅ Kategorileri Uygula", key="catrev_apply", disabled=not ok_apply):
          try:
            DATA_DIR = BASE / "data"
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            src = sqlite3.connect(DB_NAME)
            dst = sqlite3.connect(DATA_DIR / "pre_category_review.db")
            src.backup(dst)
            dst.close()
            src.close()
          except Exception:
            pass
          con = sqlite3.connect(DB_NAME)
          con.executemany(
              "UPDATE books SET category = ? WHERE id = ?",
              [(r["Önerilen"], r["ID"]) for _, r in view.iterrows()],
          )
          con.commit()
          con.close()
          st.success(f"{len(view)} kitabın kategorisi güncellendi.")
          st.rerun()

    with adm_tab_delete:
      st.subheader("🗑️ Kütüphaneden Kitap Sil")
      st.markdown("Silmek istediğiniz kitabı aratın ve kalıcı olarak kaldırın.")
      
      del_search_q = st.text_input(
          "🔍 Silinecek Kitabı Ara",
          placeholder="Kitap adı yazın...",
          key="delete_book_search",
      )
      
      matched_del_books = (
          books_df[
              books_df["title"]
              .astype(str)
              .str.contains(del_search_q.strip(), case=False, na=False)
          ]
          if del_search_q.strip()
          else pd.DataFrame()
      )

      if len(matched_del_books) > 0:
        for _, db_item in matched_del_books.iterrows():
          with st.form(f"delete_book_form_{db_item['id']}"):
            lib_type = "🏫 Okul Kitabı" if int(db_item.get("is_school", 0)) == 1 else "🏡 Ev Kitabı"
            st.error(f"📖 **{db_item['title']}** — *{db_item.get('author', 'Bilinmiyor')}* ({lib_type})")
            
            confirm_del = st.checkbox("Bu kitabı ve tüm okuma geçmişini kalıcı olarak silmeyi onaylıyorum.", key=f"chk_del_{db_item['id']}")
            
            if st.form_submit_button("Kitabı Kalıcı Olarak Sil"):
              if confirm_del:
                con = sqlite3.connect(DB_NAME)
                con.execute("DELETE FROM reading_log WHERE book_id = ?", (db_item["id"],))
                con.execute("DELETE FROM books WHERE id = ?", (db_item["id"],))
                con.commit()
                con.close()
                st.success(f"'{db_item['title']}' kütüphaneden başarıyla silindi!")
                st.rerun()
              else:
                st.warning("Lütfen silme onay kutucuğunu işaretleyin.")
      elif del_search_q.strip():
        st.info("Aradığınız kritere uygun kitap bulunamadı.")