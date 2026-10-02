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

# --- KESİN ORTALANMIŞ CSS STİLLERİ ---
st.markdown(
    """
<style>
    .stApp {
        background-color: #f8fafc !important;
        color: #1e293b;
    }
    section[data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Sekme butonlarını kesin olarak ortala */
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        justify-content: center !important;
    }
    
    .hero-container {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        border-radius: 28px;
        padding: 35px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.2);
        margin-bottom: 25px;
    }
    .hero-container h1 {
        font-size: 2.8rem;
        font-weight: 900;
        margin-bottom: 5px;
    }
    .hero-container p {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 500;
    }

    .main-card {
        background: #ffffff;
        border-radius: 24px;
        padding: 25px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.04);
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
        height: 100%;
    }
    
    .book-title {
        font-size: 1.4rem;
        color: #1e293b;
        font-weight: 800;
        margin: 15px 0 10px 0;
        text-align: center;
    }
    .book-meta {
        font-size: 0.95rem;
        color: #64748b;
        margin-bottom: 6px;
        font-weight: 500;
        text-align: center;
    }

    div.stButton > button {
        border-radius: 14px;
        font-size: 1rem;
        font-weight: 700;
        padding: 12px 20px;
        width: 100%;
        color: #ffffff !important;
        background-color: #6366f1;
        border: none;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        background-color: #4f46e5;
    }
</style>
""",
    unsafe_allow_html=True,
)


def supa():
  try:
    from supabase import create_client

    url = (
        st.secrets.get("SUPABASE_URL", "")
        if hasattr(st, "secrets")
        else ""
    )
    key = (
        st.secrets.get("SUPABASE_KEY", "")
        if hasattr(st, "secrets")
        else ""
    )
    return create_client(url, key) if url and key else None
  except Exception:
    return None


SB = supa()


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
      " DEFAULT 1); CREATE TABLE IF NOT EXISTS recommendations(period_key TEXT"
      " PRIMARY KEY,book_ids TEXT,created_at TEXT,mode TEXT);"
  )
  if con.execute("select count() from books").fetchone()[0] == 0:
    SEED.parent.mkdir(parents=True, exist_ok=True)
    if SEED.exists():
      df = pd.read_csv(SEED, dtype=str).fillna("")
      df["created_at"] = datetime.now(TZ).isoformat()
      df["read_count"] = 0
      if "cover_url" in df.columns:
        df["cover_url"] = df["cover_url"].apply(
            lambda x: "" if "longitood.com" in str(x) else x
        )
      df.to_sql("books", con, if_exists="append", index=False)
      con.commit()
  else:
    con.execute(
        "UPDATE books SET cover_url = '' WHERE cover_url LIKE"
        " '%longitood.com%'"
    )
    con.commit()
  return con


db()


def rows(table):
  if SB:
    return SB.table(table).select("").execute().data
  con = db()
  r = [dict(x) for x in con.execute(f"select * from {table}").fetchall()]
  con.close()
  return r


def insert(table, payload):
  if SB:
    SB.table(table).insert(payload).execute()
    return
  con = db()
  cols = ",".join(payload)
  q = ",".join(["?"] * len(payload))
  con.execute(
      f"insert into {table} ({cols}) values ({q})", list(payload.values())
  )
  con.commit()
  con.close()


def cover(url):
  if not url or str(url).strip() == "" or str(url).lower() == "nan":
    return None
  if "longitood.com" in str(url):
    return None
  return str(url).strip()


@st.cache_data
def get_books_df():
  con = sqlite3.connect(DB_NAME)
  df = pd.read_sql("SELECT * FROM books", con)
  con.close()
  if "read_count" not in df.columns:
    df["read_count"] = 0
  else:
    df["read_count"] = pd.to_numeric(df["read_count"], errors="coerce").fillna(0)
  return df


books_df = get_books_df()

if "selected_category" not in st.session_state:
  st.session_state.selected_category = "Tümü"
if "current_featured_books" not in st.session_state:
  st.session_state.current_featured_books = []
if "admin_logged_in" not in st.session_state:
  st.session_state.admin_logged_in = False

# --- SOL KENAR ÇUBUĞU ---
with st.sidebar:
  st.markdown(
      "<h3 style='color: #1e293b;'>🏆 Okuma Karnesi</h3>",
      unsafe_allow_html=True,
  )
  total_books = len(books_df)
  read_books = len(books_df[books_df["read_count"] > 0])
  progress_perc = read_books / total_books if total_books > 0 else 0
  st.metric(label="Okunan Kitap", value=f"{read_books} / {total_books}")
  st.progress(progress_perc)

  st.markdown("---")
  st.caption("🏰 Atlas'ın Sihirli Kütüphanesi v2.5")

# --- ÜST HERO ALANI ---
st.markdown(
    """
    <div class="hero-container">
        <h1>🏰 Atlas'ın Sihirli Kütüphanesi 📚</h1>
        <p>Bugün hangi harika maceraya yelken açmak istersin?</p>
    </div>
""",
    unsafe_allow_html=True,
)


# --- DETAY MODALI (POPUP) ---
@st.dialog("📖 Kitap Detayları", width="large")
def show_book_detail(b_id):
  b_row = books_df[books_df["id"] == b_id]
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
    st.markdown(f"🔄 **Toplam Okunma Sayısı:** {b.get('read_count', 0)}")
    st.markdown(f"⏱️ **En Son Okunma Tarihi:** {last_read_time}")

  if st.button("Kapat", use_container_width=True):
    st.rerun()


# --- ANA SEKMELER ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🎡 Sihirli Çark",
    "📖 Kütüphane & Arama",
    "🏆 Okuma Yolculuğu",
    "⚙️ Yönetici Paneli",
])

# 1. SEKME: SİHİRLİ ÇARK
with tab1:
  now = datetime.now(TZ)

  if now.hour >= 19:
    st.info(
        "🌙 Saat 19:00’dan sonra uyku öncesi huzur için yalnızca **Hikaye**"
        " kitapları seçiliyor."
    )
  else:
    st.info(
        "☀️ Gündüz kuşağı aktif: Bilgi, aktivite, ilk okuma ve hikaye kitapları"
        " keşif için hazır!"
    )

  st.markdown(
      "<h4 style='text-align: center; color: #475569; margin-bottom: 15px;'>✨"
      " Keşfetmek İstediğin Dünyayı Seç</h4>",
      unsafe_allow_html=True,
  )

  cat_cols = st.columns([1, 1, 1, 1, 1])
  categories = [
      ("🌟 Tümü", "Tümü"),
      ("🐉 Hikaye", "Hikaye"),
      ("🚀 Bilgi & Keşif", "Bilgi & Keşif"),
      ("🦁 Aktivite", "Aktivite"),
      ("💡 İlk Okuma", "İlk Okuma"),
  ]

  for idx, (label, cat_key) in enumerate(categories):
    with cat_cols[idx]:
      if st.button(label, key=f"cat_btn_{cat_key}", use_container_width=True):
        st.session_state.selected_category = cat_key
        st.session_state.current_featured_books = []
        st.rerun()

  st.markdown("<br>", unsafe_allow_html=True)

  col_spin1, col_spin2, col_spin3 = st.columns([1, 2, 1])
  with col_spin2:
    if st.button("🎲 SİHİRLİ ÇARKI ÇEVİR!", use_container_width=True):
      pool_df = (
          books_df
          if st.session_state.selected_category == "Tümü"
          else books_df[
              books_df["category"] == st.session_state.selected_category
          ]
      )
      if len(pool_df) > 0:
        unread_pool = pool_df[pool_df["read_count"] == 0]
        target_pool = unread_pool if len(unread_pool) > 0 else pool_df
        sample_n = min(2, len(target_pool))
        st.session_state.current_featured_books = (
            target_pool.sample(n=sample_n).to_dict(orient="records")
        )
      st.rerun()

  current_pool = (
      books_df
      if st.session_state.selected_category == "Tümü"
      else books_df[books_df["category"] == st.session_state.selected_category]
  )
  if not st.session_state.current_featured_books and len(current_pool) > 0:
    sample_n = min(2, len(current_pool))
    st.session_state.current_featured_books = (
        current_pool.sample(n=sample_n).to_dict(orient="records")
    )

  featured_books = st.session_state.current_featured_books
  if featured_books:
    _, col_b1, col_b2, _ = st.columns([0.5, 4, 4, 0.5])
    book_columns = [col_b1, col_b2]

    for idx, book in enumerate(featured_books):
      with book_columns[idx]:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        cover_img = cover(book.get("cover_url"))

        if cover_img:
          img_html = f'<img src="{cover_img}" style="height: 180px; object-fit: contain; border-radius: 12px; margin-bottom: 10px; display: block; margin-left: auto; margin-right: auto;">'
        else:
          img_html = '<div style="font-size: 5rem; margin-bottom: 10px;">📘</div>'

        page_val = book.get("pages")
        page_display = (
            str(page_val)
            if not pd.isna(page_val)
            and str(page_val).strip() not in ["", "0", "-", "None"]
            else "-"
        )

        st.markdown(
            f"""
                {img_html}
                <div class="book-title">📖 {book['title']}</div>
                <div class="book-meta">✍️ <b>Yazar:</b> {book.get('author', 'Bilinmiyor')}</div>
                <div class="book-meta">🎯 <b>Yaş:</b> {book.get('age', '5+')} &nbsp;|&nbsp; 📂 <b>Kategori:</b> {book.get('category', 'Hikaye')}</div>
                <div class="book-meta">🏢 <b>Yayınevi:</b> {book.get('publisher', 'Bilinmiyor')}</div>
                <div class="book-meta">📄 <b>Sayfa:</b> {page_display} &nbsp;|&nbsp; 🔄 <b>Okunma:</b> {book.get('read_count', 0)}</div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "🎉 OKUDUK!", key=f"read_btn_{book['id']}", use_container_width=True
        ):
          con = sqlite3.connect(DB_NAME)
          con.execute(
              "UPDATE books SET read_count = read_count + 1 WHERE id = ?",
              (book["id"],),
          )
          con.commit()
          con.close()

          insert(
              "reading_log",
              {
                  "book_id": book["id"],
                  "status": "read",
                  "read_at": datetime.now(TZ).isoformat(),
                  "cycle": 1,
              },
          )

          st.balloons()
          st.success(f"Harika iş çıkardın Atlas! '{book['title']}' okundu! 🌟")
          st.cache_data.clear()

          refreshed_df = get_books_df()
          unread_pool = refreshed_df[refreshed_df["read_count"] == 0]
          target_pool = (
              unread_pool if len(unread_pool) > 0 else refreshed_df
          )
          if len(target_pool) > 0:
            sample_n = min(2, len(target_pool))
            st.session_state.current_featured_books = (
                target_pool.sample(n=sample_n).to_dict(orient="records")
            )
          else:
            st.session_state.current_featured_books = []
          st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
  else:
    st.info("Bu kategoride henüz kitap bulunmuyor.")

# 2. SEKME: KÜTÜPHANE VE ARAMA (Şık Açılır Menüler ile Filtreleme)
with tab2:
  st.markdown("### 📖 Kütüphane Arşivi ve Arama")

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
    cat_filter = st.selectbox(
        "Kategori Filtrele",
        ["Tümü"]
        + sorted(
            {
                b.get("category", "")
                for b in books_df.to_dict("records")
                if b.get("category")
            }
        ),
        key="lib_cat",
    )

  filtered_lib = books_df.copy()

  # Yayınevi filtresi
  if pub_filter != "Tümü":
    filtered_lib = filtered_lib[filtered_lib["publisher"] == pub_filter]

  # Arama filtresi
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

  # Kategori filtresi
  if cat_filter != "Tümü":
    filtered_lib = filtered_lib[filtered_lib["category"] == cat_filter]

  # Kitap adına göre alfabetik sırala
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

# 3. SEKME: OKUMA YOLCULUĞU
with tab3:
  st.markdown("### 🏆 Okuma Karnesi ve İstatistikler")
  total = len(books_df)
  done = len(books_df[books_df["read_count"] > 0])
  st.metric(label="Toplam Okunan Kitap", value=f"{done} / {total}")
  st.progress(done / max(total, 1))

  stories = books_df[books_df["category"] == "Hikaye"]
  story_done = len(stories[stories["read_count"] > 0])
  st.metric(
      label="Tamamlanan Hikâyeler", value=f"{story_done} / {len(stories)}"
  )
  st.progress(story_done / max(len(stories), 1))

# 4. SEKME: YÖNETİCİ PANELİ
with tab4:
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

    adm_tab1, adm_tab2, adm_tab3, adm_tab4, adm_tab5, adm_tab6 = st.tabs([
        "➕ Yeni Kitap Ekle",
        "✏️ Kapakları Hızlı Düzenle",
        "↩️ Okunmayı Geri Al",
        "📊 Okuma Özeti",
        "📝 Ham Log Geçmişi",
        "🧹 Sıfırlama Araçları",
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
            ["Hikaye", "Bilgi & Keşif", "Aktivite", "İlk Okuma", "Duygular & Yaşam"],
        )
        new_ag = st.text_input("Yaş Grubu", "5+")
        new_pg = st.number_input("Sayfa Sayısı", min_value=1, value=32)
        new_cv = st.text_input("Kapak Görsel URL")

        if st.form_submit_button("Kütüphaneye Kaydet"):
          if new_t:
            bid = "MAN-" + uuid.uuid4().hex[:8].upper()
            con = sqlite3.connect(DB_NAME)
            con.execute(
                "INSERT INTO books (id, title, author, publisher, isbn, category, age,"
                " pages, cover_url, read_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?,"
                " ?, ?, 0, ?)",
                (
                    bid,
                    new_t,
                    new_a,
                    new_p,
                    new_isbn,
                    new_c,
                    new_ag,
                    new_pg,
                    new_cv,
                    datetime.now(TZ).isoformat(),
                ),
            )
            con.commit()
            con.close()
            st.success(f"'{new_t}' başarıyla eklendi!")
            st.cache_data.clear()
            st.rerun()

    with adm_tab2:
      st.subheader("✏️ Eksik veya Hatalı Kapakları Hızlı Düzenle")
      missing_cover_books = books_df[
          books_df["cover_url"].isna() | (books_df["cover_url"] == "")
      ]
      if len(missing_cover_books) > 0:
        for _, b in missing_cover_books.iterrows():
          with st.form(f"quick_cover_{b['id']}"):
            st.write(f"📖 **{b['title']}** ({b.get('author', 'Bilinmiyor')})")
            new_url_val = st.text_input(
                "Kapak Resim URL (örn: https://...)",
                value="",
                key=f"url_in_{b['id']}",
            )
            if st.form_submit_button("Kapağı Kaydet"):
              con = sqlite3.connect(DB_NAME)
              con.execute(
                  "UPDATE books SET cover_url = ? WHERE id = ?",
                  (new_url_val, b["id"]),
              )
              con.commit()
              con.close()
              st.success(f"'{b['title']}' kapağı güncellendi!")
              st.cache_data.clear()
              st.rerun()
      else:
        st.success("Harika! Kapaksız kitap kalmadı. 🎉")

    with adm_tab3:
      st.subheader("↩️ Okunmuş Kitabı Geri Al (Okunmadı Yap)")
      read_books_df = books_df[books_df["read_count"] > 0]
      if len(read_books_df) > 0:
        for _, rb in read_books_df.iterrows():
          col_rb1, col_rb2 = st.columns([3, 1])
          with col_rb1:
            st.write(f"📖 **{rb['title']}** (Okunma: {rb['read_count']})")
          with col_rb2:
            if st.button("Geri Al", key=f"undo_read_{rb['id']}"):
              con = sqlite3.connect(DB_NAME)
              con.execute(
                  "UPDATE books SET read_count = 0 WHERE id = ?", (rb["id"],)
              )
              con.execute(
                  "DELETE FROM reading_log WHERE book_id = ?", (rb["id"],)
              )
              con.commit()
              con.close()
              st.success(f"'{rb['title']}' okunmadı olarak işaretlendi!")
              st.cache_data.clear()
              st.rerun()
      else:
        st.info("Okundu olarak işaretlenmiş kitap bulunmuyor.")

    with adm_tab4:
      st.subheader("📊 Okuma Geçmişi Özeti")
      logs_list = rows("reading_log")
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
      for _, b in books_df.iterrows():
        b_id = b["id"]
        if b_id in summary_map:
          summary_data.append({
              "Kitap Adı": b["title"],
              "Yazar": b.get("author", "Bilinmiyor"),
              "Toplam Okunma": summary_map[b_id]["count"],
              "En Son Okunma Tarihi": summary_map[b_id]["last_read"][:19].replace(
                  "T", " "
              ),
          })

      if summary_data:
        df_summary = pd.DataFrame(summary_data).sort_values(
            by="En Son Okunma Tarihi", ascending=False
        )
        st.dataframe(df_summary, use_container_width=True)
      else:
        st.info("Henüz özetlenecek okunmuş kitap bulunmuyor.")

    with adm_tab5:
      st.subheader("📝 Ham Okuma Log Geçmişi")
      logs = rows("reading_log")
      books_list = rows("books")
      book_dict = {b["id"]: b for b in books_list}

      if logs:
        log_data = []
        for l in logs:
          b_info = book_dict.get(l["book_id"], {})
          log_data.append({
              "Kitap Adı": b_info.get("title", "Bilinmeyen Kitap"),
              "Yazar": b_info.get("author", "Bilinmiyor"),
              "Okunma Tarihi": l.get("read_at", "")[:19].replace("T", " "),
              "Durum": "Okundu ✅",
          })
        df_logs = pd.DataFrame(log_data)
        st.dataframe(df_logs, use_container_width=True)
      else:
        st.info("Henüz hiçbir kitap okunmadı.")

    with adm_tab6:
      st.subheader("🧹 Veri Sıfırlama")
      st.warning(
          "Bu buton veritabanındaki tüm okuma sayaçlarını ve okuma geçmişini"
          " sıfırlar."
      )
      if st.button("Tüm Okuma Sayaçlarını ve Geçmişi Sıfırla"):
        con = sqlite3.connect(DB_NAME)
        con.execute("UPDATE books SET read_count = 0")
        con.execute("DELETE FROM reading_log")
        con.commit()
        con.close()
        st.success("Tüm okuma karnesi başarıyla sıfırlandı!")
        st.cache_data.clear()
        st.rerun()