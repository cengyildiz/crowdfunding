"""FonDeep için kısa test betiği (Flask test istemcisi ile).

Çalıştırma:  python test_app.py
Betik veritabanındaki verileri değiştirir; bittikten sonra
`python database.py` komutuyla veritabanı sıfırlanmalıdır.
"""
from app import app
from database import SAMPLE_PASSWORD, connect, init_db


def count(table):
    conn = connect()
    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return n


def page(client, url, **kwargs):
    response = client.get(url, follow_redirects=True, **kwargs)
    return response.status_code, response.get_data(as_text=True)


def login(client, email, password, panel):
    return client.post(
        "/giris",
        data={"email": email, "password": password, "panel": panel},
        follow_redirects=True,
    ).get_data(as_text=True)


def run():
    init_db(reset=True)
    app.config["TESTING"] = True
    client = app.test_client()
    results = []

    def check(name, condition):
        results.append((name, bool(condition)))
        print(("GEÇTİ  " if condition else "KALDI  ") + name)

    # Proje listesi, arama ve kategori filtresi
    status, html = page(client, "/projeler")
    check("Proje listesi 6 projeyi gösteriyor", status == 200 and "6 proje" in html)
    _, html = page(client, "/projeler?q=Sulama")
    check("Arama yalnızca eşleşen projeyi getiriyor",
          "Akıllı Sulama Sistemi" in html and "Köy Okuluna Kütüphane" not in html)
    _, html = page(client, "/projeler?kategori=Sanat")
    check("Kategori filtresi çalışıyor",
          "Sessiz Liman" in html and "Akıllı Sulama Sistemi" not in html)

    # Giriş: yanlış ve doğru şifre
    html = login(client, "elif@fondeep.com", "yanlis-sifre", "girisimci")
    check("Yanlış şifre hata mesajı veriyor", "E-posta adresi veya şifre hatalı." in html)
    check("Hatalı girişte seçili panel korunuyor", "Girişimci Girişi" in html)
    html = login(client, "elif@fondeep.com", SAMPLE_PASSWORD, "girisimci")
    check("Girişimci paneliyle giriş yapılıyor", "Projelerim" in html)

    # Aynı hesapla iki panel ve paneller arası geçiş
    _, html = page(client, "/panel/destekci")
    check("Destekçi paneline geçiliyor", "Bağışlarım" in html)
    _, html = page(client, "/panel/girisimci")
    check("Girişimci paneline geri dönülüyor", "Projelerim" in html)
    client.get("/cikis")
    html = login(client, "elif@fondeep.com", SAMPLE_PASSWORD, "destekci")
    check("Aynı hesapla destekçi panelinden giriş yapılıyor", "Bağışlarım" in html)

    # Proje oluşturma
    before = count("projects")
    response = client.post(
        "/proje-olustur",
        data={
            "title": "Test Projesi",
            "short_desc": "Test için oluşturulan proje.",
            "description": "Bu proje test betiği tarafından oluşturulmuştur.",
            "category": "Teknoloji",
            "goal_amount": "1000",
            "deadline": "2099-01-01",
            "funding_type": "flexible",
        },
        follow_redirects=True,
    )
    check("Yeni proje kaydediliyor", count("projects") == before + 1)
    _, html = page(client, "/projeler")
    check("Yeni proje listede görünüyor", "Test Projesi" in html)
    _, html = page(client, "/panel/girisimci")
    check("Yeni proje girişimci panelinde görünüyor", "Test Projesi" in html)
    response = client.post(
        "/proje-olustur",
        data={"title": "Eksik Proje", "goal_amount": "-5", "deadline": "2000-01-01"},
        follow_redirects=True,
    )
    check("Eksik veya hatalı proje kaydedilmiyor", count("projects") == before + 1)
    client.get("/cikis")

    # Bağış
    _, html = page(client, "/projeler/5")
    check("Bağıştan önce 6.500 ₺ ve %43 görünüyor", "6.500 ₺" in html and "%43" in html)
    response = client.post(
        "/projeler/5/bagis",
        data={"amount": "500", "donor_name": "Test Destekçi", "message": ""},
        follow_redirects=True,
    )
    html = response.get_data(as_text=True)
    check("Bağıştan sonra 7.000 ₺ ve %47 görünüyor", "7.000 ₺" in html and "%47" in html)
    check("Teşekkür mesajı gösteriliyor", "500 ₺ tutarındaki bağışınız için teşekkür ederiz." in html)
    before = count("donations")
    client.post("/projeler/5/bagis", data={"amount": "0"}, follow_redirects=True)
    check("Sıfır tutarlı bağış kaydedilmiyor", count("donations") == before)

    # Kayıt formu doğrulaması (kayıt kapalı: veritabanına yazılmaz)
    users_before = count("users")
    html = client.post("/kayit", data={"name": "", "email": "yeni@fondeep.com", "password": ""}).get_data(as_text=True)
    check("Boş alanlar için uyarı gösteriliyor",
          "Ad soyad alanı boş bırakılamaz." in html and "Şifre alanı boş bırakılamaz." in html)
    html = client.post("/kayit", data={"name": "Yeni Kullanıcı", "email": "yeni@fondeep.com", "password": "123456"}).get_data(as_text=True)
    check("Dolu formda kaydın aktif olmadığı bildiriliyor", "Kayıt işlemi henüz aktif değildir." in html)
    check("Kayıt denemesi kullanıcı sayısını değiştirmiyor", count("users") == users_before)

    passed = sum(1 for _, ok in results if ok)
    print(f"\n{passed}/{len(results)} kontrol geçti.")
    return passed == len(results)


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)
