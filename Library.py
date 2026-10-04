from datetime import date, datetime, timedelta
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

# --- CSS STİLLERİ ---
st.markdown(
    """
<style>
    .stApp {
        background-color: #f8fafc !important;
        color: #1e293b;
    }
    section[data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    
    .hero-container {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #9333ea 100%);
        border-radius: 20px;
        padding: 20px 25px;
        color: white;
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.2);
        margin-bottom: 15px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .hero-container h1 {
        font-size: 2rem;
        font-weight: 900;
        margin-bottom: 4px;
    }
    .hero-container p {
        font-size: 1rem;
        opacity: 0.95;
        font-weight: 500;
        margin-bottom: 0px;
    }
    
    .sidebar-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 6px 8px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        text-align: center;
        margin-bottom: 4px;
    }

    div.stButton > button {
        border-radius: 10px;
        font-size: 0.78rem !important;
        font-weight: 700;
        padding: 6px 4px !important;
        width: 100%;
        color: #ffffff !important;
        background-color: #6366f1;
        border: none;
        box-shadow: 0 2px 6px rgba(99, 102, 241, 0.2);
        transition: all 0.2s ease;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        background-color: #4f46e5;
    }
</style>
""",
    unsafe_allow_html=True,
)


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

# --- SOL KENAR ÇUBUĞU ---
with st.sidebar:
  st.markdown(
      """
        <div style="text-align: center; margin-bottom: 0px;">
            <div style="font-size: 2.5rem; line-height: 1.1;">🏰</div>
            <h3 style="color: #1e293b; margin: 0; font-weight: 800; font-size: 0.95rem;">Atlas'ın Sihirli Kütüphanesi</h3>
            <p style="color: #64748b; font-size: 0.7rem; margin: 0px 0;">Keşfet • Oku • Hayal Et</p>
        </div>
    """,
      unsafe_allow_html=True,
  )
  st.markdown("<hr style='margin: 3px 0;'>", unsafe_allow_html=True)

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

  st.markdown("<hr style='margin: 3px 0;'>", unsafe_allow_html=True)
  st.markdown(
      "<h5 style='color: #1e293b; font-size: 0.8rem; text-align:"
      " center; margin: 1px 0;'>🏆 Okuma Künyesi</h5>",
      unsafe_allow_html=True,
  )

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
      f"""
        <div class="sidebar-card">
            <span style="font-size: 0.7rem; color: #64748b; font-weight: 700;">📚 Toplam Kitap</span>
            <p style="font-size: 1rem; color: #1e293b; font-weight: 900; margin: 0;">{total_books}</p>
        </div>
        <div class="sidebar-card">
            <span style="font-size: 0.7rem; color: #059669; font-weight: 700;">📅 Bu Ay ({current_month_name})</span>
            <p style="font-size: 1rem; color: #1e293b; font-weight: 900; margin: 0;">{month_read_count}</p>
        </div>
        <div class="sidebar-card">
            <span style="font-size: 0.7rem; color: #d97706; font-weight: 700;">🌟 Bu Yıl ({current_year})</span>
            <p style="font-size: 1rem; color: #1e293b; font-weight: 900; margin: 0;">{year_read_count}</p>
        </div>
        <div style="text-align: center; margin-top: 1px;">
            <span style="font-size: 0.65rem; color: #94a3b8; font-weight: 600;">🏰 Atlas'ın Sihirli Kütüphanesi v5.7</span>
        </div>
    """,
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


# --- SAYFA YÖNETİMİ ---
active_page = st.session_state.nav_page

# 1. ANA SAYFA
if active_page == "Ana Sayfa":
  col_h1, col_h2 = st.columns([2.2, 1])
  with col_h1:
    st.markdown(
        """
            <div class="hero-container">
                <h1>Merhaba Atlas! 👋</h1>
                <p>Bugün hangi harika maceraya yelken açmak istersin? Her kitap seni yeni bir maceraya götürür. ✨</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
  with col_h2:
    st.markdown(
        "<div style='height: 5px;'></div>", unsafe_allow_html=True
    )

    now_check = datetime.now(TZ)
    if now_check.hour >= 19:
      pool_df = books_df[books_df["category"] != "Aktivite"]
    else:
      pool_df = books_df

    # SİHİRLİ ÇARK: 2 KİTAP ÖNERİR
    if st.button("🎡 Sihirli Çarkı Çevir", use_container_width=True):
      if len(pool_df) > 0:
        unread_pool = pool_df[pool_df["read_count"] == 0]
        target_pool = unread_pool if len(unread_pool) > 0 else pool_df
        sample_n = min(2, len(target_pool))
        st.session_state.current_featured_books = (
            target_pool.sample(n=sample_n).to_dict(orient="records")
        )
      st.rerun()

    st.markdown(
        "<div style='height: 6px;'></div>", unsafe_allow_html=True
    )
    # RASTGELE ÖNER: 4 KİTAP ÖNERİR
    if st.button("📚 Rastgele Kitap Öner", use_container_width=True):
      if len(pool_df) > 0:
        st.session_state.current_featured_books = (
            pool_df.sample(n=min(4, len(pool_df)))
            .to_dict(orient="records")
        )
      st.rerun()

  # 19:00 Sonrası Uyarı Notu
  st.info(
      "🌙 Saat 19:00’dan sonra uyku öncesi huzur için **Aktivite** haricindeki"
      " tüm kitaplar seçiliyor."
  )

  st.markdown("#### ✨ Keşfetmek İstediğin Dünyayı Seç")

  cat_cols = st.columns(7)
  categories = [
      ("🌟", "Tümü"),
      ("🐉", "Hikaye"),
      ("🚀", "Bilgi"),
      ("🦁", "Aktivite"),
      ("💡", "İlk Okuma"),
      ("🌍", "Doğa"),
      ("🔬", "Bilim"),
  ]

  for idx, (icon, cat_key) in enumerate(categories):
    with cat_cols[idx]:
      actual_cat = (
          "Bilgi & Keşif"
          if cat_key == "Bilgi"
          else ("Doğa & Hayvanlar" if cat_key == "Doğa" else cat_key)
      )
      if st.button(
          f"{icon} {cat_key}",
          key=f"home_cat_{cat_key}",
          use_container_width=True,
      ):
        st.session_state.home_active_category = actual_cat
        if actual_cat == "Tümü":
          sub_pool = pool_df
        else:
          sub_pool = pool_df[pool_df["category"] == actual_cat]

        if len(sub_pool) > 0:
          st.session_state.current_featured_books = (
              sub_pool.sample(n=min(4, len(sub_pool)))
              .to_dict(orient="records")
          )
        else:
          st.session_state.current_featured_books = []
        st.rerun()

  active_cat_label = st.session_state.home_active_category
  st.markdown("<br>", unsafe_allow_html=True)
  st.markdown(
      f"#### ⭐ Senin İçin Seçtiklerimiz ({active_cat_label})"
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
    home_cols = st.columns(len(featured_books))
    current_books_df = get_books_df()

    for idx, book in enumerate(featured_books):
      with home_cols[idx]:
        b_live = current_books_df[current_books_df["id"] == book["id"]]
        read_cnt = (
            int(b_live.iloc[0]["read_count"])
            if len(b_live) > 0
            else book.get("read_count", 0)
        )

        with st.container(border=True):
          c_img = cover(book.get("cover_url"))
          if c_img:
            st.markdown(
                f'<div style="height: 140px; display: flex; align-items:'
                f' center; justify-content: center;"><img src="{c_img}"'
                ' style="max-height: 140px; object-fit: contain; border-radius:'
                ' 10px;"></div>',
                unsafe_allow_html=True,
            )
          else:
            st.markdown(
                '<div style="height: 140px; display: flex; align-items: center;'
                ' justify-content: center; font-size: 4rem;">📘</div>',
                unsafe_allow_html=True,
            )

          st.markdown(
              f"<div style='font-size: 1.05rem; font-weight: 800; margin: 8px"
              f" 0; text-align: center; height: 45px; display: flex;"
              f" align-items: center; justify-content: center;'>📖"
              f" {book['title']}</div>",
              unsafe_allow_html=True,
          )
          st.markdown(
              f"<div style='font-size: 0.85rem; color: #64748b; text-align:"
              f" center; margin-bottom: 10px;'>🎯 Yaş: {book.get('age', '5+')} |"
              f" 🔄 Okunma: {read_cnt}</div>",
              unsafe_allow_html=True,
          )

          # Butonu ortalamak için sarmalayıcı ekledik
          st.markdown(
              '<div style="display: flex; justify-content: center;">',
              unsafe_allow_html=True,
          )
          if st.button("🔍 Detay & Oku", key=f"home_det_{book['id']}"):
            show_book_detail(book["id"])
          st.markdown("</div>", unsafe_allow_html=True)


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
    chunk = filtered_lib.iloc[start : start + 4]
    for c_idx, (_, b) in enumerate(chunk.iterrows()):
      with cols[c_idx]:
        c_img = cover(b.get("cover_url"))
        img_html = (
            f'<img src="{c_img}" style="height: 130px; object-fit: contain;'
            ' border-radius: 8px; margin-bottom: 8px; display: block;'
            ' margin-left: auto; margin-right: auto;">'
            if c_img
            else '<div style="font-size: 3.5rem; margin-bottom: 8px; text-align: center;">📘</div>'
        )

        st.markdown(
            f"""
            <div style="background: white; border-radius: 20px; padding: 15px; border: 1px solid #e2e8f0; height: 240px; margin-bottom: 15px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.03); display: flex; flex-direction: column; justify-content: space-between; align-items: center;">
                <div>
                    {img_html}
                    <h4 style="font-size: 1rem; color: #1e293b; margin: 5px 0; font-weight: 700; line-height: 1.2;">{b['title']}</h4>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🔍 Detaylar", key=f"det_{b['id']}", use_container_width=True):
          show_book_detail(b["id"])


# 3. OKUMA YOLCULUĞU
elif active_page == "Okuma Yolculuğu":
  st.markdown("### 🏆 Okuma Karnesi ve Detaylı İstatistikler")

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
  st.markdown("### ⚙️ Yönetici Kontrol Paneli")

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