"""FonDeep veritabanı: tablolar ve örnek veriler.

`python database.py` komutu veritabanını siler ve örnek verilerle yeniden kurar.
"""
import os
import sqlite3
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fondeep.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id      INTEGER NOT NULL REFERENCES users(id),
    title         TEXT    NOT NULL,
    short_desc    TEXT    NOT NULL,
    description   TEXT    NOT NULL,
    category      TEXT    NOT NULL,
    goal_amount   REAL    NOT NULL CHECK (goal_amount > 0),
    funding_type  TEXT    NOT NULL CHECK (funding_type IN ('fixed', 'flexible')),
    deadline      TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS donations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id     INTEGER REFERENCES users(id),
    donor_name  TEXT    NOT NULL,
    amount      REAL    NOT NULL CHECK (amount > 0),
    message     TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

# Bütün örnek kullanıcılar aynı şifreyi kullanır.
SAMPLE_PASSWORD = "fondeep123"

SAMPLE_USERS = [
    ("Elif Yılmaz", "elif@fondeep.com"),
    ("Can Demir", "can@fondeep.com"),
    ("Zeynep Kaya", "zeynep@fondeep.com"),
    ("Mert Aydın", "mert@fondeep.com"),
    ("Ayşe Şahin", "ayse@fondeep.com"),
    ("Burak Çelik", "burak@fondeep.com"),
]

# (sahip, başlık, kısa açıklama, açıklama, kategori, hedef, fonlama modeli, kalan gün)
SAMPLE_PROJECTS = [
    (
        "Elif Yılmaz",
        "Akıllı Sulama Sistemi",
        "Toprak nemini ölçüp bitkileri kendi kendine sulayan düşük maliyetli cihaz.",
        "Cihaz, toprağa yerleştirilen nem sensöründen aldığı veriye göre küçük bir su "
        "pompasını çalıştırır. Hedefimiz ilk 200 cihazın üretimini yapmak ve mobil "
        "uygulama üzerinden sulama geçmişini göstermektir.",
        "Teknoloji",
        50000,
        "fixed",
        24,
    ),
    (
        "Can Demir",
        "Köy Okuluna Kütüphane",
        "Kars'taki bir köy okuluna 1.000 kitaplık bir kütüphane kuruyoruz.",
        "Okulun boş duran bir sınıfını kütüphaneye çeviriyoruz. Toplanan tutar raf, "
        "masa ve kitap alımı için kullanılacaktır. Kitap listesi öğretmenlerle "
        "birlikte hazırlanmıştır.",
        "Eğitim",
        30000,
        "flexible",
        12,
    ),
    (
        "Zeynep Kaya",
        "Bağımsız Kısa Film: Sessiz Liman",
        "İzmir'de geçen, balıkçı bir ailenin hikâyesini anlatan kısa film.",
        "Yirmi dakikalık filmin çekimleri Foça'da yapılacaktır. Bütçe; ekipman "
        "kiralama, oyuncu ve ekip giderleri ile kurgu ve ses tasarımı için "
        "planlanmıştır.",
        "Sanat",
        80000,
        "fixed",
        40,
    ),
    (
        "Elif Yılmaz",
        "Geri Dönüştürülmüş Plastikten Sırt Çantası",
        "Okyanustan toplanan plastik şişelerden üretilen dayanıklı sırt çantaları.",
        "Her çanta yaklaşık 25 plastik şişeden elde edilen kumaşla üretilir. İlk "
        "üretim partisi 500 çanta olacak ve destekçilere kampanya bitiminden sonra "
        "gönderilecektir.",
        "Çevre",
        40000,
        "fixed",
        6,
    ),
    (
        "Can Demir",
        "Sokak Hayvanları İçin Kış Barınakları",
        "Mahallelere yalıtımlı, taşınabilir 50 kış barınağı yerleştiriyoruz.",
        "Gönüllülerle birlikte üreteceğimiz barınaklar geri dönüştürülmüş malzemeden "
        "yapılacaktır. Toplanan tutar kadar barınak üretilecektir.",
        "Sosyal Sorumluluk",
        15000,
        "flexible",
        18,
    ),
    (
        "Mert Aydın",
        "Kampüs Ders Notu Paylaşım Uygulaması",
        "Üniversite öğrencilerinin ders notlarını paylaşabildiği mobil uygulama.",
        "Öğrenciler ders ve dönem bilgisine göre not yükleyip arayabilecek. Bütçe; "
        "sunucu giderleri ve uygulamanın mağazalarda yayınlanması için kullanılacaktır.",
        "Teknoloji",
        60000,
        "fixed",
        30,
    ),
]

# (proje başlığı, bağışçı adı, hesabı var mı, tutar, mesaj)
SAMPLE_DONATIONS = [
    ("Akıllı Sulama Sistemi", "Can Demir", True, 15000, "Kolay gelsin!"),
    ("Akıllı Sulama Sistemi", "Zeynep Kaya", True, 10000, None),
    ("Akıllı Sulama Sistemi", "Ayşe Şahin", True, 7500, "Balkonum için bekliyorum."),
    ("Köy Okuluna Kütüphane", "Mert Aydın", True, 12000, "Çocuklar için."),
    ("Köy Okuluna Kütüphane", "Anonim", False, 7500, None),
    ("Köy Okuluna Kütüphane", "Elif Yılmaz", True, 8000, None),
    ("Bağımsız Kısa Film: Sessiz Liman", "Ayşe Şahin", True, 12000, None),
    ("Geri Dönüştürülmüş Plastikten Sırt Çantası", "Mert Aydın", True, 20000, None),
    ("Geri Dönüştürülmüş Plastikten Sırt Çantası", "Burak Çelik", True, 12000, "Harika bir fikir."),
    ("Geri Dönüştürülmüş Plastikten Sırt Çantası", "Can Demir", True, 10000, None),
    ("Sokak Hayvanları İçin Kış Barınakları", "Mert Aydın", True, 4000, None),
    ("Sokak Hayvanları İçin Kış Barınakları", "Zeynep Kaya", True, 2500, None),
    ("Kampüs Ders Notu Paylaşım Uygulaması", "Burak Çelik", True, 3000, None),
]


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def seed(conn):
    """Örnek kullanıcıları, projeleri ve bağışları ekler."""
    password_hash = generate_password_hash(SAMPLE_PASSWORD)
    user_ids = {}
    for name, email in SAMPLE_USERS:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        user_ids[name] = cur.lastrowid

    project_ids = {}
    today = date.today()
    for owner, title, short_desc, description, category, goal, funding_type, days in SAMPLE_PROJECTS:
        cur = conn.execute(
            "INSERT INTO projects (owner_id, title, short_desc, description, category,"
            " goal_amount, funding_type, deadline) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_ids[owner],
                title,
                short_desc,
                description,
                category,
                goal,
                funding_type,
                (today + timedelta(days=days)).isoformat(),
            ),
        )
        project_ids[title] = cur.lastrowid

    for title, donor, has_account, amount, message in SAMPLE_DONATIONS:
        conn.execute(
            "INSERT INTO donations (project_id, user_id, donor_name, amount, message)"
            " VALUES (?, ?, ?, ?, ?)",
            (project_ids[title], user_ids[donor] if has_account else None, donor, amount, message),
        )
    conn.commit()


def init_db(reset=False):
    """Tabloları oluşturur. Veritabanı boşsa örnek verileri yükler."""
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = connect()
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        seed(conn)
    conn.close()


if __name__ == "__main__":
    init_db(reset=True)
    print("Veritabanı sıfırlandı ve örnek veriler yüklendi:", DB_PATH)
