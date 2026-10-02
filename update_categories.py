import sqlite3

DB_NAME = "atlas_library.db"

def update_book_categories():
    con = sqlite3.connect(DB_NAME)
    cursor = con.cursor()
    
    # İlk Okuma kategorisinde olup, başlığında veya yayınevinde "Cin Ali" geçmeyenleri bul ve Hikaye yap
    cursor.execute("""
        UPDATE books 
        SET category = 'Hikaye' 
        WHERE category = 'İlk Okuma' 
          AND title NOT LIKE '%Cin Ali%' 
          AND publisher NOT LIKE '%Cin Ali%'
    """)
    
    affected_rows = cursor.rowcount
    con.commit()
    con.close()
    
    print(f"✅ İşlem başarılı! Toplam {affected_rows} kitabın kategorisi 'Hikaye' olarak güncellendi.")

if __name__ == "__main__":
    update_book_categories()