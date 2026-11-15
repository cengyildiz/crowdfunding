# FonDeep

FonDeep, girişimcilerin projelerini sunduğu ve destekçilerin bu projelere bağış
yaptığı bir kitle fonlama platformudur. Python, Flask ve SQLite ile geliştirilmiştir.
CEN317 Engineering Design dersi projesidir.

## Kurulum

```
pip install -r requirements.txt
python app.py
```

Site http://127.0.0.1:5000 adresinde açılır. Uygulama ilk kez çalıştığında
`fondeep.db` dosyası oluşturulur ve örnek veriler (6 kullanıcı, 6 proje,
13 bağış) yüklenir.

## Örnek hesaplar

Bütün örnek hesapların şifresi `fondeep123` şeklindedir.

| Ad | E-posta |
|---|---|
| Elif Yılmaz | elif@fondeep.com |
| Can Demir | can@fondeep.com |
| Zeynep Kaya | zeynep@fondeep.com |
| Mert Aydın | mert@fondeep.com |
| Ayşe Şahin | ayse@fondeep.com |
| Burak Çelik | burak@fondeep.com |

Aynı hesapla hem destekçi hem girişimci panelinden giriş yapılabilir.

## Fonlama modelleri

- **Hedef Bazlı Fonlama:** Süre sonunda hedefe ulaşılırsa fon proje sahibine
  aktarılır, ulaşılamazsa bağışlar iade edilir.
- **Esnek Fonlama:** Hedefe ulaşılmasa da toplanan fon proje sahibine aktarılır.

Toplanan tutar ve proje durumu veritabanında saklanmaz; bağış kayıtlarından
her seferinde hesaplanır.

## Veritabanını sıfırlama ve test

```
python database.py     # veritabanını siler, örnek verileri yeniden yükler
python test_app.py     # test betiği (verileri değiştirir, sonra sıfırlayın)
```

## Bu aşamada olmayanlar

- Yeni kullanıcı kaydı kapalıdır (form ve alan doğrulaması çalışır).
- Bağışlar simülasyondur, gerçek ödeme alınmaz.
- Proje açıklamalarının LLM ile özetlenmesi final aşamasında eklenecektir.
