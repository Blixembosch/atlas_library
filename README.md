# Atlas Library

SQLite tabanlı, Streamlit ile hazırlanmış ev tipi okuma takip uygulaması.

## Özellikler

- Kitap ekleme, katalogda arama ve gruba göre filtreleme
- Çocuklar için uygun, anlaşılır kitap grupları
- Okunmamış kitaplara öncelik veren iki kitap önerisi
- Okunma sayısı, son okuma tarihi ve okuma karnesi
- Okuma kaydını sıfırlama ve kitap silme
- Verilerin yerel SQLite veritabanında kalıcı saklanması

## Kurulum

Projeyi kendi bilgisayarınızda çalıştırmak için terminalde proje klasörünüze gittikten sonra sırasıyla şu komutları çalıştırın:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run Library.py
