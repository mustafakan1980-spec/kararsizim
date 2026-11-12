# Kararsızım 🤔

İnsanların kararsız kaldığı konularda diğer kullanıcılara danışabildiği basit ve eğlenceli bir anket platformu.

---

## 🌟 Özellikler

- **Anket Oluşturma:** Üye kullanıcılar 2–5 seçenekli anketler açabilir.
- **Topluluk Akışı:** Herkes platformdaki tüm anketleri görür, kişiselleştirilmiş veya kapalı akış yoktur.
- **Çift Yönlü Oy Verme:** Hem giriş yapmış üyeler hem de misafir ziyaretçiler anketlere tek tıkla oy verebilir.
- **Canlı Yüzde Çubukları:** Oy verildiğinde sayfa yenilenmeden animasyonlu çubuklarla anında güncellenir.
- **Oy Değiştirme:** Fikir değiştiren kullanıcılar farklı bir seçeneğe tıklayarak oyunu güncelleyebilir.
- **Gizlilik Önceliği:** Kullanıcı e-postaları hiçbir ekranda veya API yanıtında asla görünmez. IP veya parmak izi takibi yapılmaz; misafir oyları `kz_anon` çereziyle tutulur.

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| **Backend** | Python 3.12+ / Django |
| **Veritabanı** | Supabase (PostgreSQL - Supavisor Connection Pooler) |
| **Ön Yüz** | Django Şablonları, Saf HTML5, Modern Vanilla CSS & JavaScript |
| **Kimlik Doğrulama** | Django Auth (Oturum / Cookie tabanlı) |
| **Hosting** | Vercel Serverless Python Runtime |

---

## 🚀 Yerel Geliştirme Kurulumu

### 1. Depoyu Klonlayın ve Sanal Ortamı Hazırlayın

```powershell
# Depoyu klonlayın
git clone https://github.com/mustafakan1980-spec/kararsizim.git
cd kararsizim

# Sanal ortamı kurun ve aktifleştirin (Windows)
python -m venv .venv
.\.venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 2. Ortam Değişkenleri (.env)

`.env.example` dosyasını `.env` olarak kopyalayın:

```powershell
cp .env.example .env
```

`.env` içeriği:
```env
SECRET_KEY=gizli-gelistirme-anahtari
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.vercel.app
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,https://*.vercel.app
DATABASE_URL=postgresql://postgres.sfcopfuakofjtysphptg:SIFRE@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
```

> **Not:** `DATABASE_URL` tanımlanmazsa yerel geliştirmede otomatik olarak SQLite veritabanı kullanılır.

### 3. Veritabanını Güncelleyin ve Sunucuyu Başlatın

```powershell
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py runserver
```

Tarayıcınızdan `http://127.0.0.1:8000/` adresine giderek uygulamayı görüntüleyebilirsiniz.

---

## 🗄️ Supabase Yapılandırması

Proje Supabase üzerinde `eu-central-1` (Frankfurt) bölgesinde barındırılmaktadır.

- **Yerel Migrate Portu (Session Mode):** `5432`
- **Canlı / Vercel Portu (Transaction Mode):** `6543`
- **Row Level Security (RLS):** Django tabloları `public` şemasında açıldığı için, Supabase REST API'sini kapatmak amacıyla tüm tablolarda RLS açılmıştır.

---

## ☁️ Vercel Deployment Adımları

1. Reponuzu GitHub'a push edin:
   ```powershell
   git push origin main
   ```
2. [Vercel Dashboard](https://vercel.com) üzerinden repoyu içeri aktarın (Import).
3. **Environment Variables** bölümüne şunları ekleyin:
   - `SECRET_KEY`: Güçlü rastgele gizli anahtar
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `.vercel.app,alan-adiniz.com`
   - `CSRF_TRUSTED_ORIGINS`: `https://*.vercel.app,https://alan-adiniz.com`
   - `DATABASE_URL`: Supabase Transaction Pooler adresi (Port `6543`)
4. **Deploy**'a tıklayın. Vercel `WSGI_APPLICATION` ve `STATIC_ROOT` ayarlarını otomatik okuyarak statik dosyaları CDN üzerinden sunacaktır.

---

## ⚠️ Bilinen Sınırlamalar (Prototip)

- **Misafir Oyları:** Misafir oyları `kz_anon` çerezinde tutulur. Ziyaretçi tarayıcı çerezlerini temizlerse tekrar oy verebilir. Bu, prototip için kabul edilmiş bir sınırlamadır (kullanıcı gizliliği için IP veya parmak izi takibi yapılmamaktadır).
- **Misafirlikten Üyeliğe Geçiş:** Anonim oy kullanan biri daha sonra üye olduğunda eski anonim oyları hesaba bağlanmaz.
