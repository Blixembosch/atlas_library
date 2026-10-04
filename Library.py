from datetime import date, datetime, timedelta
import html
import os
from pathlib import Path
import random
import sqlite3
import uuid
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Atlas'ın Sihirli Kütüphanesi", page_icon="🏰", layout="wide"
)

DB_NAME = "atlas_library.db"
BASE = Path(__file__).parent
SEED = BASE / "data" / "books.csv"
TZ = ZoneInfo("Europe/Amsterdam")

# --- CSS STİLLERİ (v0.6.5 - Ana Sayfada Aktivite Butonu Gizlendi) ---
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
  padding:22px 26px;box-shadow:var(--shadow);margin-bottom:18px;}
.hero-title{font-size:1.8rem;font-weight:900;color:#fff;margin-bottom:2px;}
.hero-sub{color:#fff;opacity:.95;margin:0 0 12px;font-weight:500;font-size:.95rem;}
.hero-xp{color:#fff;font-size:.9rem;margin-bottom:14px;}
.hero-xp .xp-track{background:rgba(255,255,255,.3);}
.hero-xp .xp-fill{background:#fff;}
.st-key-hero_box div.stButton>button{background:#fff;color:#4F7CFF!important;box-shadow:none;}

/* XP bar (shared) */
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


def akilli_kategori_belirle(title, author, subcategory=""):
  t = str(title).lower()
  a = str(author).lower()
  sub = str(subcategory).lower()
  combined = f"{t} {a} {sub}"

  if "çin ali" in combined or "cin ali" in combined:
    return "İlk Okuma"

  bilim_kelimeler = [
      "bilim",
      "matematik",
      "problem",
      "kg",
      "kilogram",
      "ölç",
      "sayı",
      "uzay",
      "deney",
      "fizik",
      "kimya",
      "gezegeni",
      "robot",
      "kodlama",
      "mucit",
      "icat",
      "dünya",
      "evren",
      "yıldız",
  ]
  if any(k in combined for k in bilim_kelimeler):
    return "Bilim"
  return None


def db():
  con = sqlite3.connect(DB_NAME, check_same_thread=False)
  con.row_factory = sqlite3.Row
  con.executescript(
      "CREATE TABLE IF NOT EXISTS books(id TEXT PRIMARY KEY,title TEXT NOT"
      " NULL,publisher TEXT,pages INTEGER,author TEXT,isbn TEXT,age"
      " TEXT,category TEXT,subcategory TEXT,cover_url TEXT,language TEXT"
      " DEFAULT 'Türkçe',read_count INTEGER DEFAULT 0,created_at TEXT); "
      "CREATE TABLE IF NOT EXISTS reading_log(id INTEGER PRIMARY KEY"
      " AUTOINCREMENT,book_id TEXT,status TEXT,read_at TEXT,cycle INTEGER"
      " DEFAULT 1);"
  )

  cursor = con.cursor()
  cursor.execute("PRAGMA table_info(books)")
  columns = [col["name"] for col in cursor.fetchall()]
  if "language" not in columns:
    cursor.execute("ALTER TABLE books ADD COLUMN language TEXT DEFAULT 'Türkçe'")
    con.commit()

  if con.execute("select count() from books").fetchone()[0] == 0:
    SEED.parent.mkdir(parents=True, exist_ok=True)
    if SEED.exists():
      df = pd.read_csv(SEED, dtype=str).fillna("")
      df["created_at"] = datetime.now(TZ).isoformat()
      df["read_count"] = 0
      if "language" not in df.columns:
        df["language"] = "Türkçe"
      if "cover_url" in df.columns:
        df["cover_url"] = df["cover_url"].apply(
            lambda x: "" if "longitood.com" in str(x) else x
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
    con.commit()

  all_b = con.execute(
      "SELECT id, title, author, subcategory, category FROM books"
  ).fetchall()
  for b in all_b:
    smart = akilli_kategori_belirle(
        b["title"], b["author"], b["subcategory"]
    )
    if smart:
      con.execute("UPDATE books SET category = ? WHERE id = ?", (smart, b["id"]))
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
  if "longitood.com" in str(url):
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
  return df


books_df = get_books_df()

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


total_read_books = int((books_df["read_count"] > 0).sum())
lvl = calculate_level(total_read_books)


def get_pool_df():
  df = get_books_df()
  if datetime.now(TZ).hour >= 19:
    df = df[df["category"] != "Aktivite"]
  return df


def spin_wheel():
  pool = get_pool_df()
  if len(pool) == 0:
    return
  unread = pool[pool["read_count"] == 0]
  target = unread if len(unread) > 0 else pool
  st.session_state.current_featured_books = target.sample(
      n=min(2, len(target))
  ).to_dict(orient="records")


def random_pick():
  pool = get_pool_df()
  if len(pool) > 0:
    st.session_state.current_featured_books = pool.sample(
        n=min(4, len(pool))
    ).to_dict(orient="records")


def pick_category(cat):
  st.session_state.home_active_category = cat
  pool = get_pool_df()
  sub = pool if cat == "Tümü" else pool[pool["category"] == cat]
  st.session_state.current_featured_books = (
      sub.sample(n=min(4, len(sub))).to_dict(orient="records")
      if len(sub) > 0
      else []
  )


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

  total_books = len(books_df)
  logs_data = rows("reading_log")

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
          '<div class="side-ver">Atlas v0.6.5</div>',
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
  book_logs = [l for l in logs_list if l.get("book_id") == b_id]
  last_read_time = "Henüz okunmadı"
  if book_logs:
    sorted_logs = sorted(
        book_logs, key=lambda x: x.get("read_at", ""), reverse=True
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
          '<div style="font-size: 6rem; text-align: center;">📘</div>',
          unsafe_allow_html=True,
      )
  with col_d2:
    st.markdown(f"### {b['title']}")
    st.markdown(f"✍️ **Yazar:** {b.get('author', 'Bilinmiyor')}")
    st.markdown(f"🏢 **Yayınevi:** {b.get('publisher', 'Bilinmiyor')}")
    st.markdown(f"📌 **ISBN Numarası:** {b.get('isbn', 'Bulunmuyor')}")
    st.markdown(f"📄 **Sayfa Sayısı:** {b.get('pages', '-')}")
    st.markdown(
        f"📂 **Kategori:** {b.get('category', '-')} &nbsp;|&nbsp; 🎯 **Yaş:**"
        f" {b.get('age', '-')}"
    )
    st.markdown(f"🌍 **Kitap Dili:** {b.get('language', 'Türkçe')}")
    st.markdown(f"🔄 **Toplam Okunma Sayısı:** {int(b.get('read_count', 0))}")
    st.markdown(f"⏱️ **En Son Okunma Tarihi:** {last_read_time}")

  st.markdown("---")
  st.markdown("#### 📅 Geçmiş Okuma Tarihi Gir")
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
      st.success(
          f"'{b['title']}' başarıyla {selected_date} tarihiyle kaydedildi! 🎉"
      )
      st.rerun()

  if st.button("Kapat", use_container_width=True):
    st.rerun()


# Ortak Kitap Kartı
def book_card(b, prefix, cover_h=170):
  rc = int(b.get("read_count", 0) or 0)
  img = cover(b.get("cover_url"))
  cover_html = (
      f'<img src="{html.escape(img)}">' if img else '<span style="font-size:4rem">📘</span>'
  )
  badge = "⭐ Çok Sevildi" if rc >= 3 else ("🏷️ Yeni" if rc == 0 else "")
  badge_html = f'<div class="book-badge">{badge}</div>' if badge else ""
  try:
    pages = int(float(b.get("pages")))
  except (TypeError, ValueError):
    pages = "-"
  st.markdown(
      "".join([
          f'<div class="book-card" style="height:{cover_h + 150}px">{badge_html}',
          f'<div class="book-cover" style="height:{cover_h}px">{cover_html}</div>',
          f'<div class="book-title">{html.escape(str(b["title"]))}</div>',
          f'<div class="book-meta">👶 {html.escape(str(b.get("age", "-")))}'
          f'<br>📄 {pages} Sayfa<br>🔄 {rc} Kez Okundu</div></div>',
      ]),
      unsafe_allow_html=True,
  )
  if st.button("📖 Hemen Oku", key=f"{prefix}_{b['id']}", use_container_width=True):
    show_book_detail(b["id"])


# --- SAYFA YÖNETİMİ ---
active_page = st.session_state.nav_page

# 1. ANA SAYFA
if active_page == "Ana Sayfa":
  pool_df = get_pool_df()
  active_cat_label = st.session_state.home_active_category

  with st.container(key="hero_box"):
    st.markdown(
        "".join([
            '<div class="hero-title">👋 Merhaba Atlas</div>',
            '<div class="hero-sub">Bugün seni yeni maceralar bekliyor. Her kitap yeni bir dünyadır. ✨</div>',
            f'<div class="hero-xp"><b>⭐ Seviye {lvl["level"]}</b>{level_bar_html(lvl)}</div>',
        ]),
        unsafe_allow_html=True,
    )
    hb1, hb2, _sp = st.columns([1, 1, 2])
    hb1.button("🎡 Sihirli Çark", key="hero_wheel", on_click=spin_wheel, use_container_width=True)
    hb2.button("📚 Rastgele Öner", key="hero_random", on_click=random_pick, use_container_width=True)

  st.caption("🌙 Saat 19:00’dan sonra uyku öncesi huzur için Aktivite haricindeki tüm kitaplar seçilir.")

  st.markdown("#### ✨ Keşfetmek İstediğin Dünyayı Seç")
  # Aktivite kategorisi ana sayfa buton listesinden çıkarıldı, ancak DB ve diğer sayfalarda aktif.
  categories = [
      ("🌟", "Tümü", "Tümü"), ("🐉", "Hikaye", "Hikaye"),
      ("🚀", "Bilgi", "Bilgi & Keşif"),
      ("💡", "İlk Okuma", "İlk Okuma"), ("🌍", "Doğa", "Doğa & Hayvanlar"),
      ("🔬", "Bilim", "Bilim"),
  ]
  cat_counts = books_df["category"].value_counts().to_dict()
  cat_cols = st.columns(len(categories))
  for idx, (icon, label, actual) in enumerate(categories):
    n = len(books_df) if actual == "Tümü" else cat_counts.get(actual, 0)
    is_on = active_cat_label == actual
    cat_cols[idx].button(
        f"{icon} **{label}**\n\n{n} kitap",
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

  featured_books = st.session_state.current_featured_books
  if not featured_books or len(featured_books) == 0:
    default_pool = (
        pool_df[pool_df["category"] == active_cat_label]
        if active_cat_label != "Tümü"
        else pool_df
    )
    n_default = 2 if len(featured_books) == 0 and len(default_pool) >= 2 else 4
    if len(default_pool) >= n_default:
      featured_books = default_pool.sample(n=n_default).to_dict(
          orient="records"
      )
    elif len(default_pool) > 0:
      featured_books = default_pool.to_dict(orient="records")
    elif len(pool_df) > 0:
      featured_books = pool_df.sample(
          n=min(2, len(pool_df))
      ).to_dict(orient="records")
    st.session_state.current_featured_books = featured_books

  if featured_books:
    home_cols = st.columns(4)
    for idx, book in enumerate(featured_books[:4]):
      with home_cols[idx]:
        live = books_df[books_df["id"] == book["id"]]
        book_card(live.iloc[0] if len(live) else book, "home", 170)

  st.markdown("#### 📖 Son Maceraların")
  title_map = dict(zip(books_df["id"], books_df["title"]))
  recent, seen = [], set()
  for l in sorted(logs_data, key=lambda x: x.get("read_at") or "", reverse=True):
    bid = l.get("book_id")
    if bid in title_map and bid not in seen:
      seen.add(bid)
      recent.append((title_map[bid], (l.get("read_at") or "")[:10]))
    if len(recent) == 5:
      break
  if recent:
    st.markdown(
        "".join(
            f'<div class="recent-item"><div>📖 <b>{html.escape(str(t))}</b></div><span>{d}</span></div>'
            for t, d in recent
        ),
        unsafe_allow_html=True,
    )
  else:
    st.info("Henüz okunan kitap yok. İlk maceranı başlat! 🚀")


# 2. KÜTÜPHANE
elif active_page == "Kütüphane":
  st.markdown("### 📖 Kütüphane Arşivi")

  all_publishers = sorted(
      {
          str(p).strip()
          for p in books_df["publisher"].dropna()
          if str(p).strip() != ""
      }
  )

  col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
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
    cat_options = [
        "Tümü",
        "Hikaye",
        "Bilgi & Keşif",
        "Aktivite",
        "İlk Okuma",
        "Doğa & Hayvanlar",
        "Bilim",
    ]
    default_cat_idx = (
        cat_options.index(st.session_state.selected_category)
        if st.session_state.selected_category in cat_options
        else 0
    )
    cat_filter = st.selectbox(
        "Kategori Filtrele", cat_options, index=default_cat_idx, key="lib_cat"
    )

  filtered_lib = books_df.copy()
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
      ("🏠 Ev", 0), ("✈️ Havalimanı", 5), ("🚂 Tren İstasyonu", 10),
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

  total_books_count = len(books_df)
  read_books_df = books_df[books_df["read_count"] > 0]
  total_read_count = len(read_books_df)

  total_pages_read = 0
  for _, rbook in read_books_df.iterrows():
    try:
      p = int(rbook.get("pages", 0) or 0)
      rc = int(rbook.get("read_count", 1) or 1)
      total_pages_read += p * rc
    except Exception:
      pass

  col_m1, col_m2, col_m3 = st.columns(3)
  with col_m1:
    st.metric(
        label="Toplam Okunan Kitap",
        value=f"{total_read_count} / {total_books_count}",
    )
    st.progress(
        total_read_count / max(total_books_count, 1),
        text=f"%{round((total_read_count / max(total_books_count, 1)) * 100, 1)}",
    )
  with col_m2:
    st.metric(label="Toplam Okunan Sayfa", value=f"{total_pages_read} Sayfa 📄")
  with col_m3:
    stories = books_df[books_df["category"] == "Hikaye"]
    story_done = len(stories[stories["read_count"] > 0])
    st.metric(
        label="Tamamlanan Hikâyeler", value=f"{story_done} / {len(stories)}"
    )
    st.progress(
        story_done / max(len(stories), 1),
        text=f"%{round((story_done / max(len(stories), 1)) * 100, 1)}",
    )

  st.markdown("---")
  st.markdown("#### 📊 Kategoriye Göre Okuma Dağılımı")

  cat_groups = (
      books_df.groupby("category")
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
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Kitap", total_books)
    k2.metric("Okuma Kaydı", len(logs_data))
    k3.metric("Bu Ay", month_read_count)
    k4.metric("Kapağı Eksik", missing_n)

    st.markdown("---")

    (
        adm_tab1,
        adm_tab2,
        adm_tab3,
        adm_missing_covers,
        adm_tab4,
        adm_tab5,
        adm_tab6,
        adm_tab7,
        adm_tab8,
    ) = st.tabs([
        "➕ Yeni Kitap",
        "✏️ Düzenle",
        "🎨 Kapaklar",
        "🖼️ Eksik Görseller",
        "↩ Geri Al",
        "📊 Özet",
        "📝 Loglar",
        "🧹 Sıfırla",
        "💾 DB Yedek",
    ])

    with adm_tab1:
      with st.form("admin_add_form"):
        st.subheader("Yeni Kitap Ekle")
        new_t = st.text_input("Kitap Adı")
        new_a = st.text_input("Yazar")
        new_p = st.text_input("Yayınevi")
        new_isbn = st.text_input("ISBN Numarası")
        new_c = st.selectbox(
            "Kategori",
            [
                "Hikaye",
                "Bilgi & Keşif",
                "Aktivite",
                "İlk Okuma",
                "Doğa & Hayvanlar",
                "Bilim",
            ],
        )
        new_ag = st.text_input("Yaş Grubu", "5+")
        new_pg = st.number_input("Sayfa Sayısı", min_value=1, value=32)
        new_lang = st.text_input("Kitap Dili", "Türkçe")
        new_cv = st.text_input("Kapak Görsel URL")

        if st.form_submit_button("Kütüphaneye Kaydet"):
          if new_t:
            bid = "MAN-" + uuid.uuid4().hex[:8].upper()
            con = sqlite3.connect(DB_NAME)
            con.execute(
                "INSERT INTO books (id, title, author, publisher, isbn, category, age,"
                " pages, language, cover_url, read_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?,"
                " ?, ?, ?, 0, ?)",
                (
                    bid,
                    new_t,
                    new_a,
                    new_p,
                    new_isbn,
                    new_c,
                    new_ag,
                    new_pg,
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
            up_lang = st.text_input(
                "Dil", value=str(eb.get("language", "Türkçe"))
            )
            if st.form_submit_button("Güncelle"):
              con = sqlite3.connect(DB_NAME)
              con.execute(
                  "UPDATE books SET title = ?, author = ?, publisher = ?, language ="
                  " ? WHERE id = ?",
                  (up_title, up_author, up_pub, up_lang, eb["id"]),
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
      st.subheader("🖼️ Görseli Eksik Olan Kitaplar ve Hızlı Kapak Ekleme")
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
                "SELECT id FROM reading_log WHERE book_id = ? ORDER BY read_at"
                " DESC LIMIT 1",
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
      logs_list = rows("reading_log")
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