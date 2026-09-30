import random
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Atlas'ın Sihirli Kütüphanesi", page_icon="🏰", layout="centered"
)

DB_NAME = "atlas_library.db"

# --- BÜTÜNCÜL VE DERLİ TOPLU CSS TASARIMI ---
st.markdown(
    """
<style>
    .stApp {
        background-color: #f7f5f0 !important;
        color: #2c3e50;
    }
    section[data-testid="stSidebar"] {
        background-color: #e8ede6 !important;
        border-right: 1px solid #d5dad2;
    }
    
    .main-container {
        background: #ffffff;
        border-radius: 24px;
        padding: 30px;
        box-shadow: 0 8px 25px rgba(45, 71, 57, 0.06);
        border: 1px solid #d5dad2;
        margin-bottom: 30px;
    }
    
    .main-title {
        font-size: 2.5rem;
        color: #2d4739;
        text-align: center;
        font-weight: 900;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #5c7665;
        text-align: center;
        font-weight: 600;
        margin-bottom: 25px;
    }
    
    div.stButton > button {
        border-radius: 12px;
        font-size: 0.95rem;
        font-weight: 600;
        padding: 10px 10px;
        width: 100%;
        color: #ffffff !important;
        background-color: #5c7665;
        border: none;
        box-shadow: 0 2px 6px rgba(92, 118, 101, 0.15);
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        background-color: #4a5f52;
    }

    .hero-book-card {
        background: #fbfbf9;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(45, 71, 57, 0.05);
        border: 2px solid #e2e8df;
        text-align: center;
        margin-top: 20px;
    }
    .book-title {
        font-size: 1.6rem;
        color: #2d4739;
        font-weight: 900;
        margin: 10px 0;
    }
    .book-info {
        font-size: 1rem;
        color: #4a5f52;
        margin-bottom: 6px;
        font-weight: 500;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def get_books_from_db():
  conn = sqlite3.connect(DB_NAME)
  df = pd.read_sql("SELECT * FROM books", conn)
  conn.close()
  return df


books_df = get_books_from_db()

if "selected_category" not in st.session_state:
  st.session_state.selected_category = "Tümü"
if "current_featured_book" not in st.session_state:
  st.session_state.current_featured_book = None
if "admin_mode" not in st.session_state:
  st.session_state.admin_mode = False

# --- SOL KENAR ÇUBUĞU ---
with st.sidebar:
  st.markdown(
      "<h3 style='color: #2d4739;'>🏆 Okuma Karnesi</h3>", unsafe_allow_html=True
  )
  total_books = len(books_df)
  read_books = (
      len(books_df[books_df["read_count"] > 0])
      if "read_count" in books_df.columns
      else 0
  )
  progress_perc = read_books / total_books if total_books > 0 else 0
  st.metric(label="Okunan Kitap", value=f"{read_books} / {total_books}")
  st.progress(progress_perc)

  st.markdown("---")
  st.markdown("<h3 style='color: #2d4739;'>🔍 Arama</h3>", unsafe_allow_html=True)
  arama_metni = st.text_input("Kitap / Yazar Ara", placeholder="Kelime yazın...")

  if "publisher" in books_df.columns:
    yayinevleri = sorted(books_df["publisher"].dropna().unique().tolist())
    secilen_yayinevi = st.multiselect(
        "Yayınevi", options=yayinevleri, default=[]
    )
  else:
    secilen_yayinevi = []

  secilen_durum = st.selectbox("Durum", ["Tümü", "Okundu", "Okunacak"])

  st.markdown("---")
  st.markdown("<h3 style='color: #2d4739;'>🔐 Yönetim</h3>", unsafe_allow_html=True)
  admin_pass = st.text_input("Şifre", type="password")

  if admin_pass == "Eindhoven22!" or st.session_state.admin_mode:
    st.session_state.admin_mode = True
    st.success("Yönetim Aktif ✅")
    if st.button("Çıkış Yap"):
      st.session_state.admin_mode = False
      st.rerun()

# --- GELİŞMİŞ YÖNETİM PANELİ ---
if st.session_state.admin_mode:
  st.markdown("<hr>", unsafe_allow_html=True)
  st.markdown(
      "<h2 style='color: #2d4739; text-align: center;'>⚙️ Kütüphane Yönetim"
      " Paneli</h2>",
      unsafe_allow_html=True,
  )

  tab1, tab2, tab3 = st.tabs([
      "➕ Yeni Kitap Ekle",
      "✏️ Mevcut Kitabı Düzenle",
      "🖼️ Eksik Kapaklar (Takip & Yönetim)",
  ])

  with tab1:
    st.markdown("### Veritabanına Manuel Kitap Ekle")
    with st.form("add_book_form"):
      new_title = st.text_input("Kitap Adı")
      new_author = st.text_input("Yazar")
      new_publisher = st.text_input("Yayınevi")
      new_category = st.selectbox(
          "Kategori",
          [
              "Bilim & Keşif",
              "Matematik",
              "Macera & Masal",
              "Sevimli Hayvanlar",
              "Duygular & Yaşam",
          ],
      )
      new_age = st.selectbox("Yaş Grubu", ["3+", "5+", "6+", "7+"])
      new_cover = st.text_input(
          "Kapak Görsel URL (İsteğe bağlı - Boş bırakılırsa varsayılan"
          " kullanılır)"
      )

      submit_add = st.form_submit_button("🚀 Kitabı Veritabanına Ekle")
      if submit_add:
        if new_title:
          conn = sqlite3.connect(DB_NAME)
          cursor = conn.cursor()
          cursor.execute(
              """
                        INSERT INTO books (title, publisher, category, age_group, cover_url, read_count)
                        VALUES (?, ?, ?, ?, ?, 0)
                    """,
              (
                  new_title,
                  new_publisher,
                  new_category,
                  new_age,
                  new_cover,
              ),
          )
          conn.commit()
          conn.close()
          st.success(f"'{new_title}' başarıyla eklendi! 🎉")
          st.cache_data.clear()
          st.rerun()
        else:
          st.error("Kitap adı boş bırakılamaz!")

  with tab2:
    st.markdown("### Kitap Bilgilerini Güncelle veya Sil")
    selected_book_id = st.selectbox(
        "Düzenlenecek Kitabı Seç",
        books_df["id"].astype(str) + " - " + books_df["title"],
    )
    b_id = selected_book_id.split(" - ")[0]
    curr_book = books_df[books_df["id"].astype(str) == b_id].iloc[0]

    with st.form("edit_book_form"):
      ed_title = st.text_input("Kitap Adı", value=curr_book["title"])
      ed_publisher = st.text_input(
          "Yayınevi", value=str(curr_book.get("publisher", ""))
      )
      ed_age = st.selectbox(
          "Yaş Grubu",
          ["3+", "5+", "6+", "7+"],
          index=(
              ["3+", "5+", "6+", "7+"].index(curr_book.get("age_group", "5+"))
              if curr_book.get("age_group") in ["3+", "5+", "6+", "7+"]
              else 1
          ),
      )
      ed_cover = st.text_input(
          "Kapak Görsel URL", value=str(curr_book.get("cover_url", ""))
      )

      col_e1, col_e2 = st.columns(2)
      with col_e1:
        submit_update = st.form_submit_button("💾 Güncellemeleri Kaydet")
      with col_e2:
        submit_delete = st.form_submit_button("🗑️ Kitabı Sil")

      if submit_update:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
                    UPDATE books SET title = ?, publisher = ?, age_group = ?, cover_url = ? WHERE id = ?
                """,
            (ed_title, ed_publisher, ed_age, ed_cover, b_id),
        )
        conn.commit()
        conn.close()
        st.success("Kitap güncellendi! ✅")
        st.cache_data.clear()
        st.rerun()

      if submit_delete:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = ?", (b_id,))
        conn.commit()
        conn.close()
        st.warning("Kitap silindi! 🗑️")
        st.cache_data.clear()
        st.rerun()

  with tab3:
    st.markdown("### 🖼️ Kapak Görseli Eksik Olan Kitaplar")
    missing_df = books_df[
        books_df["cover_url"].isna() | (books_df["cover_url"] == "")
    ]
    st.info(f"Toplam {len(missing_df)} adet kapaksız kitap bulunuyor.")

    if len(missing_df) > 0:
      st.dataframe(
          missing_df[["id", "title", "publisher", "category"]],
          use_container_width=True,
      )

      st.markdown("#### Hızlı Kapak Ekle / Düzelt")
      selected_missing_id = st.selectbox(
          "Düzenlemek İstediğin Eksik Kitabı Seç",
          missing_df["id"].astype(str) + " - " + missing_df["title"],
          key="missing_selectbox",
      )
      m_id = selected_missing_id.split(" - ")[0]
      m_curr = missing_df[missing_df["id"].astype(str) == m_id].iloc[0]

      with st.form("quick_cover_form"):
        st.write(f"**Seçilen Kitap:** {m_curr['title']}")
        new_url_input = st.text_input("Kapak Resim URL Adresi")
        submit_quick_cover = st.form_submit_button(
            "✨ Kapak URL'sini Kaydet ve Güncelle"
        )

        if submit_quick_cover:
          if new_url_input:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE books SET cover_url = ? WHERE id = ?",
                (new_url_input, m_id),
            )
            conn.commit()
            conn.close()
            st.success("Kapak başarıyla eklendi! 🎉")
            st.cache_data.clear()
            st.rerun()
          else:
            st.error("Lütfen geçerli bir URL yazın.")
    else:
      st.success(
          "Harika! Veritabanında kapaksız hiçbir kitap kalmamış. Tüm"
          " kapaklar tam yerinde! 🚀"
      )

# --- ANA EKRAN ---
st.markdown(
    '<p class="main-title">🏰 Atlas\'ın Sihirli Kütüphanesi 📚</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="sub-title">Bugün hangi maceraya odaklanmak istersin?</p>',
    unsafe_allow_html=True,
)

# Filtreleme Mantığı
filtered_main_df = books_df.copy()
if arama_metni:
  mask = filtered_main_df["title"].str.contains(arama_metni, case=False, na=False)
  filtered_main_df = filtered_main_df[mask]

if secilen_yayinevi:
  filtered_main_df = filtered_main_df[
      filtered_main_df["publisher"].isin(secilen_yayinevi)
  ]

if secilen_durum == "Okundu":
  filtered_main_df = filtered_main_df[filtered_main_df["read_count"] > 0]
elif secilen_durum == "Okunacak":
  filtered_main_df = filtered_main_df[filtered_main_df["read_count"] == 0]

if arama_metni or secilen_yayinevi or secilen_durum != "Tümü":
  st.markdown(
      f"### 🔎 Filtrelenmiş Sonuçlar ({len(filtered_main_df)} Kitap)"
  )
  st.dataframe(
      filtered_main_df[["title", "publisher", "category", "read_count"]],
      use_container_width=True,
  )
  st.markdown("---")

# BÜTÜNCÜL KAPSAYICI BAŞLANGICI
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown(
    "<h4"
    " style='color: #2d4739; margin-top: 0; text-align: center;'>✨ Adım 1: Macera"
    " Türünü Seç</h4>",
    unsafe_allow_html=True,
)

cat_cols = st.columns(3)
categories = [
    ("🌟 Tümü", "Tümü"),
    ("🚀 Bilim & Keşif", "Bilim & Keşif"),
    ("📐 Matematik", "Matematik"),
    ("🐉 Macera & Masal", "Macera & Masal"),
    ("🦁 Hayvanlar", "Sevimli Hayvanlar"),
    ("💡 Duygular", "Duygular & Yaşam"),
]

for idx, (label, cat_key) in enumerate(categories):
  with cat_cols[idx % 3]:
    is_selected = st.session_state.selected_category == cat_key
    btn_label = f"✓ {label}" if is_selected else label
    if st.button(btn_label, key=f"cat_{cat_key}"):
      st.session_state.selected_category = cat_key
      st.session_state.current_featured_book = None
      st.rerun()

st.markdown(
    f"<p style='text-align: center; color: #5c7665; margin-top: 10px;"
    f" margin-bottom: 10px; font-weight: bold; font-size: 0.95rem;'>Seçilen:"
    f" <span style='color: #2d4739;'>{st.session_state.selected_category}</span></p>",
    unsafe_allow_html=True,
)

st.markdown("<hr style='margin: 15px 0; border-color: #e8ede6;'>", unsafe_allow_html=True)

st.markdown(
    "<h4"
    " style='color: #2d4739; margin-top: 0; text-align: center;'>✨ Adım 2: Sürpriz"
    " Kitabını Getir</h4>",
    unsafe_allow_html=True,
)

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
  if st.button("🎲 SİHİRLİ ÇARKI ÇEVİR!"):
    filtered_df = (
        books_df
        if st.session_state.selected_category == "Tümü"
        else books_df[
            books_df["category"] == st.session_state.selected_category
        ]
    )


    def get_random_book(pool_df):
      if len(pool_df) == 0:
        return None
      unread_pool = (
          pool_df[pool_df["read_count"] == 0]
          if "read_count" in pool_df.columns
          else pool_df
      )
      target_pool = unread_pool if len(unread_pool) > 0 else pool_df
      return target_pool.sample(n=1).iloc[0].to_dict()


    st.session_state.current_featured_book = get_random_book(filtered_df)
    st.rerun()

# Otomatik ilk kitap ataması
filtered_df = (
    books_df
    if st.session_state.selected_category == "Tümü"
    else books_df[books_df["category"] == st.session_state.selected_category]
)
if not st.session_state.current_featured_book:
  unread_pool = (
      filtered_df[filtered_df["read_count"] == 0]
      if "read_count" in filtered_df.columns
      else filtered_df
  )
  target_pool = unread_pool if len(unread_pool) > 0 else filtered_df
  if len(target_pool) > 0:
    st.session_state.current_featured_book = (
        target_pool.sample(n=1).iloc[0].to_dict()
    )

# --- GERÇEK KİTAP KAPAĞI GÖSTERİMİ ---
book = st.session_state.current_featured_book
if book:
  cover_img = book.get("cover_url")

  st.markdown('<div class="hero-book-card">', unsafe_allow_html=True)

  if cover_img and not pd.isna(cover_img) and str(cover_img).strip() != "":
    try:
      st.image(str(cover_img).strip(), width=220)
    except Exception:
      st.info("Kapak görseli yüklenemedi.")
  else:
    st.info("Bu kitap için görsel eklenmemiş.")

  st.markdown(
      f"""
        <div class="book-title">📖 {book['title']}</div>
        <div class="book-info">🎯 <b>Yaş:</b> {book.get('age_group', '5+')} &nbsp;|&nbsp; 🏷️ <b>Tür:</b> {book.get('main_category', 'Okuma')}</div>
        <div class="book-info">🏢 <b>Yayınevi:</b> {book['publisher']} &nbsp;|&nbsp; 📂 <b>Kategori:</b> {book['category']}</div>
        <div class="book-info">📄 <b>Sayfa:</b> {book.get('page_count', '-')} &nbsp;|&nbsp; 🔄 <b>Okunma:</b> {book.get('read_count', 0)}</div>
    </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown("<br>", unsafe_allow_html=True)
  col_a1, col_a2, col_a3 = st.columns([1, 2, 1])
  with col_a2:
    if st.button(f"🎉 BU KİTABI OKUDUK! ({book['title']})"):
      conn = sqlite3.connect(DB_NAME)
      cursor = conn.cursor()
      cursor.execute(
          """
                UPDATE books 
                SET read_count = read_count + 1, last_read_date = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
          (book["id"],),
      )
      conn.commit()
      conn.close()
      st.balloons()
      st.success(f"Harika iş çıkardın Atlas! '{book['title']}' okundu! 🌟")
      unread_pool = (
          filtered_df[filtered_df["read_count"] == 0]
          if "read_count" in filtered_df.columns
          else filtered_df
      )
      target_pool = unread_pool if len(unread_pool) > 0 else filtered_df
      if len(target_pool) > 0:
        st.session_state.current_featured_book = (
            target_pool.sample(n=1).iloc[0].to_dict()
        )
      else:
        st.session_state.current_featured_book = None
      st.rerun()
else:
  st.info("Bu kategoride henüz kitap bulunmuyor.")

st.markdown("</div>", unsafe_allow_html=True)