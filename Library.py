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
        background-color: #f1f5f9 !important;
        border-right: 1px solid #e2e8f0;
    }
    
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
    
    .cat-box {
        background: #ffffff;
        border-radius: 20px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        text-align: center;
        margin-bottom: 15px;
    }

    .sidebar-card {
        background: #ffffff;
        border-radius: 18px;
        padding: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        text-align: center;
        margin-bottom: 12px;
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
if "selected_pub_filter" not in st.session_state:
  st.session_state.selected_pub_filter = "Tümü"

# --- SOL KENAR ÇUBUĞU (KÜNYE) ---
with st.sidebar:
  st.markdown(
      "<h3 style='color: #1e293b; margin-bottom: 0px; text-align:"
      " center;'>🏆 Okuma Künyesi</h3>",
      unsafe_allow_html=True,
  )
  st.markdown("---")

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
            <h4 style="color: #4f46e5; margin-bottom: 4px; font-weight: 800; font-size: 1rem;">📚 Toplam Kitap</h4>
            <p style="font-size: 1.6rem; color: #1e293b; font-weight: 900; margin: 0;">{total_books}</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown(
      f"""
        <div class="sidebar-card">
            <h4 style="color: #059669; margin-bottom: 4px; font-weight: 800; font-size: 1rem;">📅 Bu Ay ({current_month_name})</h4>
            <p style="font-size: 1.6rem; color: #1e293b; font-weight: 900; margin: 0;">{month_read_count}</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown(
      f"""
        <div class="sidebar-card">
            <h4 style="color: #d97706; margin-bottom: 4px; font-weight: 800; font-size: 1rem;">🌟 Bu Yıl ({current_year})</h4>
            <p style="font-size: 1.6rem; color: #1e293b; font-weight: 900; margin: 0;">{year_read_count}</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown("---")
  st.caption("🏰 Atlas'ın Sihirli Kütüphanesi v2.8")

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
      st.cache_data.clear()
      st.rerun()

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

  featured_books = st.session_state.current_featured_books
  if featured_books:
    _, col_b1, col_b2, _ = st.columns([0.5, 4, 4, 0.5])
    book_columns = [col_b1, col_b2]

    current_books_df = get_books_df()

    for idx, book in enumerate(featured_books):
      with book_columns[idx]:
        b_live = current_books_df[current_books_df["id"] == book["id"]]
        read_cnt = (
            int(b_live.iloc[0]["read_count"])
            if len(b_live) > 0
            else book.get("read_count", 0)
        )
        is_read_now = read_cnt > 0

        with st.container(border=True):
          cover_img = cover(book.get("cover_url"))
          if cover_img:
            st.markdown(
                f'<div style="height: 180px; display: flex; align-items: center;'
                f' justify-content: center;"><img src="{cover_img}"'
                ' style="max-height: 180px; object-fit: contain; border-radius:'
                ' 12px;"></div>',
                unsafe_allow_html=True,
            )
          else:
            st.markdown(
                '<div style="height: 180px; display: flex; align-items: center;'
                ' justify-content: center; font-size: 5rem;">📘</div>',
                unsafe_allow_html=True,
            )

          page_val = book.get("pages")
          page_display = (
              str(page_val)
              if not pd.isna(page_val)
              and str(page_val).strip() not in ["", "0", "-", "None"]
              else "-"
          )

          status_badge = (
              '<span style="color: #15803d; font-weight: 800;">✅ OKUNDU</span>'
              if is_read_now
              else '<span style="color: #6366f1; font-weight: 800;">🎯'
              " OKUNMAYI BEKLİYOR</span>"
          )

          st.markdown(
              f"<div style='font-size: 1.3rem; color: #1e293b; font-weight:"
              f" 800; margin: 10px 0; text-align: center; min-height: 50px;"
              f" display: flex; align-items: center; justify-content:"
              f" center;'>📖 {book['title']}</div>",
              unsafe_allow_html=True,
          )
          st.markdown(
              f"<div style='font-size: 0.92rem; color: #64748b; margin-bottom:"
              f" 4px; font-weight: 500; text-align: center;'>✍️ <b>Yazar:</b>"
              f" {book.get('author', 'Bilinmiyor')}</div>",
              unsafe_allow_html=True,
          )
          st.markdown(
              f"<div style='font-size: 0.92rem; color: #64748b; margin-bottom:"
              f" 4px; font-weight: 500; text-align: center;'>🎯 <b>Yaş:</b>"
              f" {book.get('age', '5+')} &nbsp;|&nbsp; 📂 <b>Kategori:</b>"
              f" {book.get('category', 'Hikaye')}</div>",
              unsafe_allow_html=True,
          )
          st.markdown(
              f"<div style='font-size: 0.92rem; color: #64748b; margin-bottom:"
              f" 4px; font-weight: 500; text-align: center;'>🏢"
              f" <b>Yayınevi:</b> {book.get('publisher', 'Bilinmiyor')}</div>",
              unsafe_allow_html=True,
          )
          st.markdown(
              f"<div style='font-size: 0.92rem; color: #64748b; margin-bottom:"
              f" 4px; font-weight: 500; text-align: center;'>📄 <b>Sayfa:</b>"
              f" {page_display} &nbsp;|&nbsp; 🔄 <b>Okunma:</b>"
              f" {read_cnt}</div>",
              unsafe_allow_html=True,
          )
          st.markdown(
              f"<div style='margin-top: 8px; text-align:"
              f" center;'>{status_badge}</div>",
              unsafe_allow_html=True,
          )

          st.markdown("<br>", unsafe_allow_html=True)

          if not is_read_now:
            if st.button(
                "🎉 OKUDUK!", key=f"read_btn_{book['id']}", use_container_width=True
            ):
              con = sqlite3.connect(DB_NAME)
              con.execute(
                  "UPDATE books SET read_count = read_count + 1 WHERE id = ?",
                  (book["id"],),
              )
              con.execute(
                  "INSERT INTO reading_log (book_id, status, read_at, cycle)"
                  " VALUES (?, 'read', ?, 1)",
                  (book["id"], datetime.now(TZ).isoformat()),
              )
              con.commit()
              con.close()

              st.balloons()
              st.success(
                  f"Harika iş çıkardın Atlas! '{book['title']}' okundu! 🌟"
              )
              st.cache_data.clear()
              st.rerun()
          else:
            st.info("Bu kitap okundu olarak işaretlendi! 🌟")
  else:
    st.info(
        "✨ Kitapları keşfetmek için yukarıdan kategori seçip **'SİHİRLİ ÇARKI"
        " ÇEVİR'** butonuna basın!"
    )

# 2. SEKME: KÜTÜPHANE VE ARAMA
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

# 3. SEKME: OKUMA YOLCULUĞU
with tab3:
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

  st.markdown("#### 📚 En Son Okunan Kitaplar")
  logs_data = rows("reading_log")
  if logs_data:
    sorted_all_logs = sorted(
        logs_data, key=lambda x: x.get("read_at", ""), reverse=True
    )
    book_dict = {b["id"]: b for b in books_df.to_dict("records")}
    recent_list = []
    seen_ids = set()
    for l in sorted_all_logs:
      bid = l.get("book_id")
      if bid not in seen_ids and bid in book_dict:
        seen_ids.add(bid)
        b_info = book_dict[bid]
        recent_list.append({
            "Kitap Adı": b_info.get("title"),
            "Yazar": b_info.get("author"),
            "Kategori": b_info.get("category"),
            "Okunma Tarihi": l.get("read_at", "")[:19].replace("T", " "),
        })
      if len(recent_list) >= 10:
        break
    st.dataframe(pd.DataFrame(recent_list), use_container_width=True)
  else:
    st.info("Henüz okuma geçmişi bulunmuyor.")

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

    (
        adm_tab1,
        adm_tab2,
        adm_tab3,
        adm_tab4,
        adm_tab5,
        adm_tab6,
        adm_tab7,
        adm_tab8,
    ) = st.tabs([
        "➕ Yeni Kitap Ekle",
        "✏️ Kitap Düzenle",
        "🎨 Kapakları Düzenle",
        "↩️ Okunmayı Geri Al",
        "📊 Okuma Özeti",
        "📝 Ham Log",
        "🧹 Sıfırlama",
        "💾 Veritabanı Yedek",
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
      st.subheader("✏️ Kitap Künyesini Düzenle (Ad, Yazar, Yayınevi vb.)")
      edit_search_q = st.text_input(
          "🔍 Düzenlenecek Kitabı Ara",
          placeholder="Kitap veya yazar adı yazın...",
          key="edit_book_search",
      )

      if edit_search_q.strip():
        eq = edit_search_q.strip()
        matched_edit_books = books_df[
            books_df["title"]
            .astype(str)
            .str.contains(eq, case=False, na=False)
            | books_df["author"]
            .astype(str)
            .str.contains(eq, case=False, na=False)
        ]
      else:
        matched_edit_books = pd.DataFrame()
        st.info(
            "💡 Düzenlemek istediğiniz kitabı bulmak için yukarıdaki arama"
            " çubuğuna adını veya yazarını yazın."
        )

      if len(matched_edit_books) > 0:
        st.write(
            f"📚 Eşleşen Kitap Sayısı: **{len(matched_edit_books)}**"
        )
        for _, eb in matched_edit_books.iterrows():
          with st.form(f"edit_book_form_{eb['id']}"):
            st.markdown(f"### 📖 {eb['title']}")
            up_title = st.text_input("Kitap Adı", value=eb["title"])
            up_author = st.text_input(
                "Yazar", value=str(eb.get("author", ""))
            )
            up_pub = st.text_input(
                "Yayınevi", value=str(eb.get("publisher", ""))
            )

            cat_list = [
                "Hikaye",
                "Bilgi & Keşif",
                "Aktivite",
                "İlk Okuma",
                "Duygular & Yaşam",
            ]
            current_cat = eb.get("category", "Hikaye")
            cat_idx = (
                cat_list.index(current_cat) if current_cat in cat_list else 0
            )
            up_cat = st.selectbox("Kategori", cat_list, index=cat_idx)

            up_age = st.text_input("Yaş Grubu", value=str(eb.get("age", "5+")))
            try:
              p_val = int(eb.get("pages", 32) or 32)
            except Exception:
              p_val = 32
            up_pages = st.number_input(
                "Sayfa Sayısı", min_value=1, value=p_val
            )

            if st.form_submit_button(
                "💾 Değişiklikleri Kaydet", use_container_width=True
            ):
              con = sqlite3.connect(DB_NAME)
              con.execute(
                  """
                            UPDATE books 
                            SET title = ?, author = ?, publisher = ?, category = ?, age = ?, pages = ?
                            WHERE id = ?
                        """,
                  (
                      up_title,
                      up_author,
                      up_pub,
                      up_cat,
                      up_age,
                      up_pages,
                      eb["id"],
                  ),
              )
              con.commit()
              con.close()
              st.success(f"'{up_title}' başarıyla güncellendi! 🎉")
              st.cache_data.clear()
              st.rerun()

    with adm_tab3:
      st.subheader("🎨 Tüm Kütüphane Kapak Düzenleme ve Arama")
      cover_search_query = st.text_input(
          "🔍 Kitap veya Yazar Adına Göre Ara",
          placeholder="Örn: Denizler Altında",
          key="cover_search_input",
      )

      if cover_search_query.strip():
        q_clean = cover_search_query.strip()
        filtered_cover_books = books_df[
            books_df["title"]
            .astype(str)
            .str.contains(q_clean, case=False, na=False)
            | books_df["author"]
            .astype(str)
            .str.contains(q_clean, case=False, na=False)
        ]
      else:
        filtered_cover_books = books_df[
            books_df["cover_url"].isna() | (books_df["cover_url"] == "")
        ]
        st.caption(
            "💡 Şu an sadece kapaksız kitaplar listeleniyor. Tüm kitaplar"
            " arasında aramak için yukarıdaki kutucuğa yazın."
        )

      st.write(f"📚 Bulunan Kitap Sayısı: **{len(filtered_cover_books)}**")

      if len(filtered_cover_books) > 0:
        for _, b in filtered_cover_books.iterrows():
          with st.form(f"quick_cover_{b['id']}"):
            current_cover = b.get("cover_url")
            cover_status = (
                "✅ Kapak Var"
                if current_cover and str(current_cover).strip() != ""
                else "❌ Kapak Yok"
            )
            st.write(
                f"📖 **{b['title']}** — *{b.get('author', 'Bilinmiyor')}*"
                f" ({cover_status})"
            )
            new_url_val = st.text_input(
                "Kapak Resim URL (örn: https://...)",
                value=str(current_cover)
                if current_cover and str(current_cover) != "nan"
                else "",
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
        st.info("Aramanıza uygun kitap bulunamadı.")

    # GÜNCELLENEN SEKME: SADECE SON OKUMAYI GERİ AL (SAYAÇTAN 1 DÜŞ)
    with adm_tab4:
      st.subheader("↩️ En Son Okumayı Geri Al")
      st.info(
          "Bu işlem, ilgili kitabın sadece **en son okuma kaydını** siler ve"
          " okunma sayacından 1 düşer."
      )
      read_books_df_adm = books_df[books_df["read_count"] > 0]
      if len(read_books_df_adm) > 0:
        for _, rb in read_books_df_adm.iterrows():
          col_rb1, col_rb2 = st.columns([3, 1])
          with col_rb1:
            st.write(
                f"📖 **{rb['title']}** (Toplam Okunma:"
                f" {int(rb['read_count'])})"
            )
          with col_rb2:
            if st.button("Son Okumayı Geri Al", key=f"undo_read_{rb['id']}"):
              con = sqlite3.connect(DB_NAME)
              # Sadece en son eklenen log kaydını bul ve sil
              last_log = con.execute(
                  "SELECT id FROM reading_log WHERE book_id = ? ORDER BY"
                  " read_at DESC LIMIT 1",
                  (rb["id"],),
              ).fetchone()
              if last_log:
                con.execute(
                    "DELETE FROM reading_log WHERE id = ?", (last_log[0],)
                )
              # Sayaçtan 1 düş (0'ın altına düşmemesini sağla)
              con.execute(
                  "UPDATE books SET read_count = MAX(0, read_count - 1) WHERE id"
                  " = ?",
                  (rb["id"],),
              )
              con.commit()
              con.close()
              st.success(
                  f"'{rb['title']}' için son okuma geri alındı ve sayaç"
                  " güncellendi!"
              )
              st.cache_data.clear()
              st.rerun()
      else:
        st.info("Okundu olarak işaretlenmiş kitap bulunmuyor.")

    with adm_tab5:
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

    with adm_tab6:
      st.subheader("📝 Ham Okuma Log Geçmişi (Okunma Sayısı Dahil)")
      logs = rows("reading_log")
      books_list = rows("books")
      book_dict = {b["id"]: b for b in books_list}

      if logs:
        log_data = []
        for idx, l in enumerate(logs, start=1):
          b_info = book_dict.get(l["book_id"], {})
          log_data.append({
              "Sıra": idx,
              "Kitap Adı": b_info.get("title", "Bilinmeyen Kitap"),
              "Yazar": b_info.get("author", "Bilinmiyor"),
              "Okunma Sayısı": int(b_info.get("read_count", 0)),
              "Okunma Tarihi": l.get("read_at", "")[:19].replace("T", " "),
              "Durum": "Okundu ✅",
          })
        df_logs = pd.DataFrame(log_data)
        st.dataframe(df_logs, use_container_width=True)
      else:
        st.info("Henüz hiçbir kitap okunmadı.")

    with adm_tab7:
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

    with adm_tab8:
      st.subheader("💾 Canlı Veritabanı Yedeğini İndir")
      st.info(
          "Canlı sunucuda yapılan okumaları ve güncellemeleri kaybetmemek için"
          " bu butona basarak veritabanı yedeğini (`atlas_library.db`) indirebilir"
          " ve lokal bilgisayarınıza taşıyabilirsiniz."
      )
      if os.path.exists(DB_NAME):
        with open(DB_NAME, "rb") as f:
          st.download_button(
              label="📥 atlas_library.db Dosyasını İndir",
              data=f,
              file_name="atlas_library.db",
              mime="application/x-sqlite3",
              use_container_width=True,
          )
      else:
        st.warning("Veritabanı dosyası bulunamadı.")