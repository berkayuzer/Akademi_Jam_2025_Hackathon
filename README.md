# Akademi_Jam_2025_Hackathon

# KodAdım: Yapay Zeka Destekli Yazılım Öğrenme Platformu
## Geliştiriciler
### YZTA JAM Grup 62
- Berkay Üzer
- Tuana Korkmazyürek
- Rümeysa Nur Demirbaş
- Onur Gökdoğan
- İpek Eylül Atmaca

Bu proje, kullanıcıların programlama konularını kişiselleştirilmiş bir yol haritası ile öğrenmesini sağlayan, yapay zeka (Gemini) destekli bir eğitim platformudur. Kullanıcılar seviyelerine uygun konuları seçebilir, otomatik oluşturulan özet ve challenge’larla pratik yapabilir ve ilerlemelerini takip edebilirler.

## Özellikler

- **Kullanıcı Kaydı ve Girişi:** E-posta ve kullanıcı adı ile kayıt olma ve giriş yapma.
- **Konu ve Dil Seçimi:** Python, JavaScript, Java, C++, C#, Go, Swift, Kotlin, Ruby gibi dillerde temel programlama konularını seçme.
- **Kişisel Yol Haritası:** Seçilen konulara göre otomatik oluşturulan, adım adım öğrenme yol haritası.
- **Yapay Zeka Destekli İçerik:** Gemini API ile her konu ve adım için Türkçe özet, örnekler ve seviyelere göre challenge’lar.
- **Kod Çalıştırma ve Test:** Challenge’lar için kod yazma, örnek ve gizli testlerle anında geri bildirim.
- **İlerleme Takibi:** Tamamlanan konular ve genel ilerleme yüzdesi.
- **Modern ve Türkçe Arayüz:** Tamamen Türkçe, kullanıcı dostu ve responsive tasarım.

## Kurulum

### Gereksinimler

- Python 3.8+
- [pip](https://pip.pypa.io/en/stable/)
- [Gemini API Key](https://ai.google.dev/)

### Bağımlılıklar

Aşağıdaki komut ile gerekli paketleri yükleyin:

```bash
pip install fastapi uvicorn sqlalchemy python-dotenv google-generativeai
```

### Veritabanı Kurulumu

İlk kez çalıştırmadan önce veritabanı tablolarını oluşturun:

```bash
python create_db.py
```

### Ortam Değişkenleri

Ana dizinde `.env` dosyası oluşturun ve Gemini API anahtarınızı ekleyin:

```
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

### Uygulamayı Başlatma

```bash
uvicorn main:app --reload
```

Tarayıcıda [http://127.0.0.1:8000](http://127.0.0.1:8000) adresine gidin.

## Klasör Yapısı

```
ai-edu-fastapi/
│
├── ai/
│   └── roadmap.py         # Gemini API ile içerik ve challenge üretimi
│
├── static/
│   ├── style.css          # Özel stiller
│   └── ...                # Arkaplan görselleri
│
├── templates/
│   ├── base.html          # Ortak şablon
│   ├── login.html         # Giriş ekranı
│   ├── register.html      # Kayıt ekranı
│   ├── dashboard.html     # Konu/dil seçimi
│   ├── home.html          # İlerleme ve konu kartları
│   ├── roadmap.html       # Yol haritası
│   ├── topic_page.html    # Konu özeti ve challenge başlıkları
│   ├── step_challenge.html# Adım bazlı challenge ekranı
│   ├── challenge.html     # Kod yazma ve test ekranı
│   └── general_home.html  # Giriş yapmamış kullanıcılar için ana sayfa
│
├── database.py            # SQLAlchemy modelleri ve veritabanı bağlantısı
├── create_db.py           # Veritabanı oluşturucu
├── main.py                # FastAPI uygulaması ve endpointler
└── .env                   # Ortam değişkenleri (API anahtarı)
```

## Kullanım Akışı

1. **Kayıt Ol / Giriş Yap:** Kullanıcı hesabı oluşturun veya giriş yapın.
2. **Konu ve Dil Seçimi:** Dashboard’da öğrenmek istediğiniz dili ve konuyu seçin.
3. **Yol Haritası:** Seçtiğiniz konular için otomatik oluşturulan yol haritasını inceleyin.
4. **Adım ve Challenge:** Her adımda örnekleri ve challenge’ları çözerek pratik yapın.
5. **Kodunuzu Test Edin:** Kodunuzu yazın, örnek ve gizli testlerle anında geri bildirim alın.
6. **İlerlemenizi Takip Edin:** Tamamladığınız konular ve genel ilerlemeniz ana ekranda görüntülenir.

## Geliştirici Notları

- **Gemini API** ile içerik üretimi Türkçe olarak yapılır.
- Kod testleri Python için subprocess ile çalıştırılır.
- Kullanıcı adı, üst menüde gösterilir ve oturum yönetimi session ile sağlanır.
- Tüm arayüz ve içerikler Türkçedir.
