# Kararsızım 🤔

İnsanların kararsız kaldığı konularda diğer kullanıcılara danışabildiği basit bir anket platformu.

---

## 🛠️ Teknoloji Yığını

- **Backend:** Python 3.12+ / Django
- **Veritabanı:** Supabase (Yönetilen PostgreSQL)
- **Ön Yüz:** Django Şablonları, Vanilla CSS & JS
- **Deployment:** Vercel

---

## 🚀 Yerel Kurulum Adımları

### 1. Sanal Ortamı Hazırlama ve Bağımlılıkları Yükleme

```bash
# Sanal ortam oluştur ve etkinleştir (Windows)
python -m venv .venv
.\.venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 2. Ortam Değişkenlerini Ayarlama

`.env.example` dosyasını `.env` olarak kopyalayın:

```bash
cp .env.example .env
```

`.env` dosyasını kendi değerlerinizle güncelleyin:
- Yerelde hızlıca SQLite ile denemek isterseniz `DATABASE_URL` satırını boş bırakabilir veya yorum satırı yapabilirsiniz.
- Supabase kullanırken Supabase bağlantı adresinizi girin.

---

## 🗄️ Supabase Kurulumu (Kullanıcının Elle Yapacağı Adımlar)

1. [Supabase](https://supabase.com) üzerinde yeni bir proje oluşturun.
2. **Project Settings -> Database** bölümüne gidin.
3. **Connection Pooling (Supavisor)** adreslerini not edin:
   - **Transaction mode (Port 6543):** Canlı ortam (Vercel) ve Django çalışma zamanı için kullanılır.
   - **Session mode (Port 5432):** Yerelden `migrate` komutunu çalıştırırken kullanılır.
4. `.env` dosyanızdaki `DATABASE_URL` değerine Supabase bağlantı dizesini ekleyin.
5. Migration'ları oluşturup uygulayın:
   ```bash
   python manage.py makemigrations accounts
   python manage.py makemigrations
   python manage.py migrate
   ```
6. Süper kullanıcı oluşturun:
   ```bash
   python manage.py createsuperuser
   ```
7. **Güvenlik (RLS):** Django tabloları `public` şemasında açılır. Supabase REST API'sini yetkisiz erişime kapatmak için **Supabase SQL Editor**'e gidin ve aşağıdaki script'i çalıştırın:
   ```sql
   DO $$
   DECLARE r record;
   BEGIN
     FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
       EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', r.tablename);
     END LOOP;
   END $$;
   ```

---

## 💻 Sunucuyu Çalıştırma

```bash
python manage.py runserver
```

Tarayıcınızdan `http://127.0.0.1:8000/` adresine giderek ana sayfayı, `http://127.0.0.1:8000/admin/` adresinden yönetim panelini açabilirsiniz.

---

## ☁️ Vercel Deployment Adımları

1. Kodlarınızı GitHub reponuza gönderin:
   ```bash
   git add .
   git commit -m "Faz 0: Proje kurulumu ve altyapı"
   git push origin main
   ```
2. [Vercel](https://vercel.com) paneline gidin ve repoyu içe aktarın (Import Project).
3. **Project Settings -> Environment Variables** alanına aşağıdaki değişkenleri girin:
   - `SECRET_KEY`: Güçlü ve gizli bir anahtar
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `.vercel.app,alan-adiniz.com`
   - `CSRF_TRUSTED_ORIGINS`: `https://*.vercel.app,https://alan-adiniz.com`
   - `DATABASE_URL`: Supabase Transaction Pooler adresi (Port 6543)
4. **Deploy** butonuna tıklayın. Vercel `manage.py` ve `WSGI_APPLICATION` ayarını otomatik algılayıp `collectstatic` çalıştıracaktır.
