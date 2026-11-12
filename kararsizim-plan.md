# Kararsızım — Proje Planı ve Geliştirme Talimatları

> Bu dosya, projeyi geliştirecek yapay zekâ kod asistanı (Claude Code / Cursor) için hazırlanmıştır.
> Önce **tamamını oku**, sonra yalnızca istenen **fazı** uygula. Faz sırasını atlama, bir sonraki fazın işini önceden yapma.

---

## 1. Proje Özeti

**Kararsızım**, insanların kararsız kaldığı konularda diğer kullanıcılara danışabildiği basit bir anket platformudur.

Örnek: "Bugün sinemaya mı gitsem, restorana mı?" sorusu sorulur, 2–5 seçenek eklenir, diğer kullanıcılar oy verir.

### Temel kurallar

- Bir ankette **en az 2, en fazla 5 seçenek** olur.
- **Takip (follow) sistemi yoktur.** Herkes platformdaki her anketi görür ve oylayabilir. Kişiselleştirilmiş akış yoktur.
- **Üye olmayan** ziyaretçi anketleri görüntüleyebilir ve **oy verebilir**.
- **Anket oluşturmak için üyelik zorunludur.** Giriş yapmamış biri "Anket oluştur"a basarsa giriş/kayıt sayfasına yönlendirilir, giriş sonrası anket oluşturma sayfasına döner.
- Kayıtta **e-posta, kullanıcı adı ve parola** istenir.
- Anketlerde **kullanıcı adı** görünür, **e-posta asla** görünmez (hiçbir sayfada, hiçbir API cevabında).
- Bu bir **prototiptir**. Basit tut, gereksiz karmaşıklık ekleme. İleride adım adım geliştirilecek.

### Kapsam dışı (prototipte YAPILMAYACAK)

Takip/arkadaşlık, yorum, beğeni, bildirim, doğrudan mesaj, e-posta doğrulama, şifre sıfırlama, sosyal medya ile giriş, profil fotoğrafı, kategori/etiket, arama, çoklu dil, ödeme, React/Vue/Tailwind/Bootstrap gibi ek framework'ler, Django REST Framework, Celery/Redis. (Bazıları "Faz 5 — Sonraki adımlar" bölümünde not edilmiştir.)

---

## 2. Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.12 + Django (güncel kararlı sürüm, 5.2 LTS veya üstü) |
| Veritabanı | Supabase (yalnızca **yönetilen PostgreSQL** olarak; Supabase Auth/Storage/Realtime KULLANILMAYACAK) |
| Kimlik doğrulama | Django'nun kendi auth sistemi (oturum/cookie tabanlı) |
| Ön yüz | Django şablonları + saf HTML, CSS, JavaScript (ayrı framework yok, aynı repo) |
| Deployment | Vercel (Python runtime, Django otomatik algılanır) |
| Yardımcı paketler | `psycopg[binary]`, `dj-database-url`, `python-dotenv` |

Ön yüz için ayrı bir build adımı, npm, bundler **yoktur**. Tüm CSS/JS `static/` klasöründe düz dosyalardır.

### Vercel notları (güncel dokümana göre)

- Vercel, kök dizindeki `manage.py`'yi bulup Django projesini otomatik algılar ve giriş noktasını `settings.py` içindeki `WSGI_APPLICATION` ayarından okur. Bu nedenle `wsgi.py` içinde `application` değişkeni tanımlı olmalı ve `WSGI_APPLICATION = 'config.wsgi.application'` ayarlanmalı.
- `settings.py` içinde `STATIC_ROOT` tanımlıysa Vercel build sırasında `collectstatic` komutunu otomatik çalıştırır ve statik dosyaları CDN'den `STATIC_URL` üzerinden sunar. **WhiteNoise gerekmez.**
- Varsayılan Python sürümü 3.12'dir.
- Eğer deploy sırasında bu davranış farklı çıkarsa, kendi bildiğini varsaymadan **güncel Vercel Django dokümanına** (vercel.com/docs/frameworks/backend/django) bak.

### Supabase bağlantı notları

- Django, Supabase'e normal bir PostgreSQL gibi `DATABASE_URL` ile bağlanır.
- Vercel serverless olduğu için çalışma zamanında **Supabase connection pooler (Supavisor, transaction mode, port 6543)** bağlantı adresi kullanılmalı. Bu modda:
  - `DISABLE_SERVER_SIDE_CURSORS = True`
  - `CONN_MAX_AGE = 0`
- `migrate` komutu **yerel bilgisayardan**, pooler'ın **session mode (port 5432)** adresiyle çalıştırılır (Vercel build'inde migrate çalıştırılmaz).
- Doğrudan (direct) bağlantı adresi bazı ortamlarda yalnızca IPv6 destekler; sorun yaşanırsa pooler adresini kullan.
- **Güvenlik:** Django tabloları Supabase'in `public` şemasında oluşur ve Supabase'in otomatik REST API'si üzerinden dışarı açık olabilir. Migrate sonrası tüm tablolarda **Row Level Security (RLS) açılmalı** ve policy eklenmemeli. Django `postgres` rolüyle bağlandığı için RLS'ten etkilenmez, ama anonim API erişimi kapanır:

```sql
-- Supabase SQL Editor'de, migrate sonrası çalıştırılacak
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', r.tablename);
  END LOOP;
END $$;
```

(Yeni migration ile yeni tablo eklenirse bu script tekrar çalıştırılmalı.)

---

## 3. Proje Yapısı

```
kararsizim/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/            # kullanıcı, kayıt, giriş, çıkış, profil sayfası
│   ├── models.py        # özel User modeli
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── polls/               # anket, seçenek, oy
│   ├── models.py        # Poll, Option, Vote
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── utils.py         # anonim token yardımcıları, sonuç hesaplama
│   ├── admin.py
│   └── tests.py
├── templates/
│   ├── base.html
│   ├── partials/        # navbar, mesajlar, anket kartı
│   ├── accounts/        # login.html, register.html, profile.html
│   ├── polls/           # home.html, detail.html, create.html
│   ├── 404.html
│   └── 500.html
└── static/
    ├── css/style.css
    └── js/
        ├── main.js        # ortak: mobil menü, mesajları kapatma vb.
        ├── poll_form.js   # dinamik seçenek ekle/çıkar
        └── vote.js        # oy verme (fetch) + sonuç çubukları
```

Kod ve değişken isimleri **İngilizce**, kullanıcıya görünen tüm metinler **Türkçe** olacak. Yorum satırları kısa ve Türkçe veya İngilizce olabilir (tutarlı ol).

---

## 4. Ortam Değişkenleri (`.env.example`)

```
SECRET_KEY=degistir-beni
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.vercel.app
CSRF_TRUSTED_ORIGINS=https://*.vercel.app
DATABASE_URL=postgresql://postgres.xxxx:SIFRE@aws-0-xx.pooler.supabase.com:6543/postgres
```

- `.env` dosyası `.gitignore`'a eklenir, **asla commit edilmez**.
- Yerelde `python-dotenv` ile okunur; Vercel'de aynı değişkenler Project Settings → Environment Variables'a girilir.
- Geliştirmeyi hızlandırmak için `DATABASE_URL` tanımlı değilse yerelde SQLite'a düşülebilir (yalnızca `DEBUG=True` iken). Gerçek testler Supabase üzerinde yapılmalı.
- Production'da (`DEBUG=False`): `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` `True`; `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`.
- Diğer ayarlar: `LANGUAGE_CODE = 'tr'`, `TIME_ZONE = 'Europe/Istanbul'`, `USE_I18N = True`.

---

## 5. Veri Modeli

### 5.1 `accounts.User` (`AbstractUser`'dan türetilir)

> `AUTH_USER_MODEL = 'accounts.User'` — **ilk migration'dan önce** ayarlanmalı.

| Alan | Kural |
|---|---|
| `username` | Zorunlu, benzersiz (büyük/küçük harf duyarsız), 3–20 karakter, yalnızca harf (a-z), rakam ve `_`. Küçük harfe çevirerek kaydet. |
| `email` | Zorunlu, benzersiz (büyük/küçük harf duyarsız), küçük harfe çevirerek kaydet. **Hiçbir şablonda veya JSON'da gösterilmez.** |
| `password` | Django'nun parola doğrulayıcıları (min. 8 karakter vb.) |

Giriş: kullanıcı tek bir alana **e-posta veya kullanıcı adı** yazabilir + parola. (View içinde `email__iexact` veya `username__iexact` ile kullanıcı bulunup `authenticate` edilir.)

### 5.2 `polls.Poll`

| Alan | Tip / kural |
|---|---|
| `author` | FK → User (`on_delete=CASCADE`), `related_name='polls'` |
| `question` | CharField, max 150, zorunlu |
| `created_at` | DateTimeField, `auto_now_add`, index'li |
| `is_active` | BooleanField, varsayılan `True` (silme = `False`; yumuşak silme) |

### 5.3 `polls.Option`

| Alan | Tip / kural |
|---|---|
| `poll` | FK → Poll, `related_name='options'` |
| `text` | CharField, max 80, zorunlu |
| `position` | PositiveSmallIntegerField (0–4), sıralama için |

`Meta`: `ordering = ['position']`, `UniqueConstraint(poll, position)`.

### 5.4 `polls.Vote`

| Alan | Tip / kural |
|---|---|
| `poll` | FK → Poll, `related_name='votes'` |
| `option` | FK → Option, `related_name='votes'` |
| `user` | FK → User, **null=True**, blank=True |
| `anon_token` | CharField(64), **null=True**, blank=True, db_index |
| `created_at` | `auto_now_add` |

Kısıtlar (`Meta.constraints`):

1. `CheckConstraint`: `user` ile `anon_token`'dan **tam olarak biri** dolu olmalı.
2. `UniqueConstraint(fields=['poll', 'user'], condition=Q(user__isnull=False))`
3. `UniqueConstraint(fields=['poll', 'anon_token'], condition=Q(anon_token__isnull=False))`

Ek doğrulama (view içinde): seçilen `option`, ilgili `poll`'a ait olmalı ve poll `is_active` olmalı.

### Oy verme mantığı

- Giriş yapmış kullanıcı: oy `user` ile kaydedilir.
- Giriş yapmamış ziyaretçi: ilk oyda rastgele bir token (`uuid4().hex`) üretilir ve `kz_anon` adlı cookie'ye yazılır (`HttpOnly`, `SameSite=Lax`, `Secure` (prod), 1 yıl). Oy `anon_token` ile kaydedilir.
- Bir kişi bir ankete **tek oy** kullanabilir. Aynı ankete tekrar oy verirse oyu **güncellenir** (fikir değiştirebilir). Yeni kayıt açılmaz.
- **IP adresi veya parmak izi gibi takip yöntemleri KULLANILMAZ.** Cookie'yi silen biri tekrar oy verebilir; prototip için kabul edilen bir sınırlamadır.
- Anonim olarak oy veren biri sonradan üye olursa eski oyları birleştirilmez (prototip için gerek yok).

### Sonuç hesaplama

Oy sayıları `annotate(Count('votes'))` ile hesaplanır (ayrı sayaç alanı tutulmaz). Yüzde = `round(oy / toplam * 100)`; toplam 0 ise yüzde 0.

---

## 6. Sayfalar ve URL'ler

### Sayfalar

| URL | Yöntem | Erişim | Açıklama |
|---|---|---|---|
| `/` | GET | Herkes | Anket akışı: en yeniden eskiye, sayfa başına 12, `?sayfa=` ile sayfalama |
| `/anket/<id>/` | GET | Herkes | Anket detayı + oy verme + sonuçlar |
| `/anket/yeni/` | GET, POST | Giriş şart | Anket oluşturma formu |
| `/anket/<id>/sil/` | POST | Yalnızca sahibi | Anketi sil (yumuşak silme) |
| `/u/<username>/` | GET | Herkes | Kullanıcının anketleri (takip butonu YOK, e-posta YOK) |
| `/kayit/` | GET, POST | Misafir | Üye ol (e-posta, kullanıcı adı, parola, parola tekrarı) |
| `/giris/` | GET, POST | Misafir | Giriş (e-posta veya kullanıcı adı + parola), `?next=` desteği |
| `/cikis/` | POST | Üye | Çıkış |
| `/admin/` | — | Süper kullanıcı | Django admin (moderasyon için hazır gelir) |

### JSON uç noktaları

**`POST /anket/<id>/oy/`**

İstek (JSON): `{ "option_id": 12 }` — Başlık: `X-CSRFToken`.

Cevap 200:

```json
{
  "ok": true,
  "my_option_id": 12,
  "total": 37,
  "options": [
    { "id": 12, "text": "Sinema", "votes": 20, "percent": 54 },
    { "id": 13, "text": "Restoran", "votes": 17, "percent": 46 }
  ]
}
```

Hata: 400 (geçersiz seçenek / poll), 404 (poll yok veya silinmiş), 403 (CSRF). Hata cevabı: `{ "ok": false, "error": "Türkçe mesaj" }`.

Cevaplarda **asla** kullanıcı e-postası bulunmaz.

---

## 7. Davranış Detayları

### Anket oluşturma formu

- Soru alanı (max 150, kalan karakter göstergesi).
- Başlangıçta **2 seçenek** kutusu. "＋ Seçenek ekle" butonu ile en fazla 5'e çıkar; 5 olunca buton gizlenir/devre dışı kalır.
- 2'den fazla olan seçenekler "✕" ile silinebilir; 2'nin altına inilemez.
- Sunucu tarafı doğrulama (JS'e güvenme): boşlukları kırp, boş seçenekleri at, **büyük/küçük harf duyarsız tekrar eden seçeneklere izin verme**, geçerli seçenek sayısı 2–5 olmalı, soru boş olamaz. Hata mesajları Türkçe ve form üzerinde gösterilir.
- Başarılı oluşturma → anket detay sayfasına yönlendir + "Anketin yayında!" mesajı.
- Poll + Option kayıtları tek `transaction.atomic()` içinde oluşturulur.

### Anket detay sayfası

- Üstte: soru, "@kullaniciadi · 2 saat önce".
- Oy vermemişse: seçenekler büyük, tıklanabilir kartlar/butonlar olarak görünür. Sonuçlar **gizli**, ama altta küçük bir "Oy vermeden sonuçları gör" bağlantısı vardır.
- Oy verdikten sonra (fetch ile, sayfa yenilenmeden): seçenekler yüzde çubuklarına dönüşür, kullanıcının seçtiği vurgulanır (✓), toplam oy sayısı gösterilir. "Oyunu değiştir" mümkündür (başka seçeneğe tıklamak yeterli).
- Sayfa yenilendiğinde kullanıcının oyu (user veya `kz_anon` cookie ile) sunucu tarafında bulunur ve sonuç görünümü açık gelir.
- Anketin sahibiyse "Sil" butonu görünür (onay penceresiyle).
- JS kapalı olsa bile temel işlev için formun `<noscript>` alternatifi **gerekmez** (prototip).

### Ana sayfa

- Üstte kısa hero: başlık ("Kararsız mı kaldın? Sor, herkes oylasın 🤔") ve büyük "Anket oluştur" butonu.
- Altında anket kartları ızgarası: soru, yazar (@kullaniciadi), göreli zaman, seçenek sayısı/toplam oy, "Oy ver" butonu.
- Boş durum: "Henüz anket yok. İlk kararsız sen ol!" + buton.
- Sayfalama: "← Önceki / Sonraki →".

### Navbar

- Sol: logo "kararsızım" (+ emoji).
- Sağ (misafir): "Giriş yap" (ikincil buton), "Üye ol" (birincil buton).
- Sağ (üye): "＋ Anket oluştur" (birincil buton), "@kullaniciadi" (profil bağlantısı), "Çıkış".
- Mobilde sade: hamburger menü veya sığacak şekilde küçülen butonlar.

---

## 8. Arayüz / Tasarım Rehberi

**Hedef kitle:** gençler. **Hissiyat:** açık, temiz, canlı, eğlenceli ama dağınık değil.

### Renk paleti (CSS değişkenleri olarak `:root` içinde tanımla)

```css
:root {
  --bg: #FAFAFF;            /* açık arka plan */
  --surface: #FFFFFF;       /* kartlar */
  --ink: #1E1B3A;           /* ana metin */
  --muted: #6B6890;         /* ikincil metin */
  --border: #ECEAF7;

  --primary: #6C5CE7;       /* canlı mor — ana vurgu */
  --primary-soft: #EFECFF;
  --pink: #FF6B9D;
  --yellow: #FFD166;
  --teal: #06D6A0;
  --blue: #4CC9F0;

  --radius: 20px;
  --shadow: 0 8px 24px rgba(108, 92, 231, 0.10);
}
```

- Seçenekler için 5 renk sırayla döner: mor, pembe, sarı, turkuaz, mavi (seçenek çubukları ve kart kenarlıkları bu renklerle ton ton kullanılır; yazı kontrastı yeterli olmalı).
- Arka plan açık kalır; renk, butonlarda, çubuklarda, rozetlerde ve küçük dekoratif şekillerde (hero arkasında yumuşak bulanık daireler gibi) kullanılır.

### Tipografi

- Google Fonts'tan **Poppins** veya **Plus Jakarta Sans** (yedek: `system-ui, sans-serif`). Başlıklar kalın (700–800), gövde 400–500.

### Bileşenler

- Büyük yuvarlatılmış köşeler (16–24px), yumuşak gölgeler, bol boşluk.
- Butonlar: yuvarlak (pill) veya çok yuvarlak köşe, hover'da hafif yukarı kayma + gölge artışı.
- Anket kartı hover'da hafifçe yükselir.
- Yüzde çubukları yumuşak animasyonla dolar (`transition: width .6s ease`).
- Küçük emoji kullanımı serbest ama abartma (başlıklarda, boş durumlarda, butonlarda).
- Form alanları: büyük, yuvarlak, odaklanınca `--primary` renkli halka.
- **Mobil öncelikli** (mobile-first) yaz; 360px genişlikte sorunsuz çalışmalı. Anket kartı ızgarası: mobilde 1, tablette 2, masaüstünde 3 sütun.
- Erişilebilirlik: yeterli renk kontrastı, odak halkaları görünür, butonlarda anlamlı etiketler, `prefers-reduced-motion` için animasyonları kıs.

### Örnek Türkçe metinler

- Hero: "Kararsız mı kaldın? Sor, herkes oylasın 🤔"
- Anket oluştur: "Neye karar veremiyorsun?" / seçenek placeholder'ı: "Seçenek 1"
- Oy sonrası: "Oyun kaydedildi ✓"
- Giriş şart uyarısı: "Anket oluşturmak için önce giriş yapmalısın."
- Hata: "Bir şeyler ters gitti, tekrar dener misin?"

---

## 9. Güvenlik ve Kalite Kuralları

- Tüm kullanıcı girdileri Django şablon otomatik kaçışıyla basılır; `|safe` ve `innerHTML` ile kullanıcı metni **basma** (JS'te `textContent` kullan).
- Tüm POST istekleri CSRF korumalıdır. `fetch` isteklerinde `X-CSRFToken` başlığı gönderilir (token, şablondaki `<meta name="csrf-token">` veya cookie'den okunur). Detay sayfası view'ında `@ensure_csrf_cookie` kullan.
- `SECRET_KEY` ve veritabanı bilgileri kodda yazılmaz.
- Yetki kontrolleri sunucuda yapılır: anket oluşturma `login_required`, silme yalnızca sahibine.
- E-posta hiçbir yerde gösterilmez; `User` modelinin `__str__` metodu `username` döndürür.
- Olmayan/silinmiş anket → 404 sayfası. Özel 404/500 şablonları tasarıma uygun olmalı.
- Gereksiz bağımlılık ekleme. Bir şey için yeni paket gerekiyorsa önce kullanıcıya sor.
- Kod okunabilir ve küçük fonksiyonlardan oluşsun; sınıf tabanlı view veya fonksiyon tabanlı view — ikisinden birini seç ve tutarlı kal (fonksiyon tabanlı önerilir, prototip için daha sade).

---

## 10. Asistan İçin Çalışma Kuralları

1. Her seferinde **yalnızca istenen fazı** uygula.
2. Faz bitince şunları yap: neyi yaptığını kısa özetle, çalıştırma/test adımlarını yaz, kabul kriterlerini tek tek kontrol et, bir sonraki fazın ne olduğunu söyle ve **dur**.
3. Belirsiz bir nokta olursa varsayım yapıp ilerlemeden önce kısa bir soru sor; küçük detaylarda mantıklı varsayım yapıp bunu belirt.
4. Arayüz metinleri Türkçe, kod İngilizce.
5. Her faz sonunda uygulama **çalışır halde** olmalı (`python manage.py runserver` ile hata vermemeli).
6. Mevcut çalışan şeyleri sebepsiz yere yeniden yazma; küçük ve odaklı değişiklikler yap.

---

# FAZLAR

---

## Faz 0 — İskelet, Veritabanı Bağlantısı ve İlk Deploy

**Amaç:** Boş ama canlıya çıkabilen bir Django uygulaması; Supabase'e bağlı; Vercel'de açılıyor.

### Yapılacaklar

1. Django projesini `config` adıyla oluştur; `accounts` ve `polls` uygulamalarını ekle.
2. `requirements.txt`: `Django`, `psycopg[binary]`, `dj-database-url`, `python-dotenv`.
3. `settings.py`: bölüm 4'teki ayarlar, `DATABASE_URL` okuma (pooler uyumlu ayarlarla), `STATIC_URL='/static/'`, `STATIC_ROOT=BASE_DIR/'staticfiles'`, `STATICFILES_DIRS=[BASE_DIR/'static']`, `TEMPLATES['DIRS']=[BASE_DIR/'templates']`, `WSGI_APPLICATION='config.wsgi.application'`.
4. `wsgi.py` içinde `application` değişkeninin tanımlı olduğundan emin ol.
5. **Özel User modeli**'ni (bölüm 5.1) hemen oluştur ve `AUTH_USER_MODEL`'e bağla (ilk migration'dan önce!). Henüz kayıt/giriş sayfası yazma.
6. `base.html` ve basit bir ana sayfa ("Kararsızım yakında 🤔") oluştur; `style.css` içine renk değişkenlerini ve temel tipografiyi ekle.
7. `.gitignore`, `.env.example`, kısa bir `README.md` (yerel kurulum + Supabase + Vercel adımları) yaz.
8. `python manage.py migrate` ve `createsuperuser` çalışacak şekilde hazırla.

### Kullanıcının elle yapacağı adımlar (asistan bunları README'ye yazsın)

- Supabase'de proje aç, bağlantı adreslerini al (pooler).
- `.env` oluştur, yerelde `migrate` çalıştır, ardından bölüm 2'deki RLS script'ini Supabase SQL Editor'de çalıştır.
- Repo'yu GitHub'a it, Vercel'de içe aktar, ortam değişkenlerini gir, deploy et.

### Kabul kriterleri

- [ ] `runserver` ile `/` açılıyor, statik dosyalar yükleniyor.
- [ ] `migrate` Supabase'e karşı hatasız çalışıyor, `/admin/` açılıyor.
- [ ] Vercel'deki canlı adreste `/` ve `/static/css/style.css` açılıyor.

### Prompt

```
kararsizim-plan.md dosyasını baştan sona oku. Sadece "Faz 0"ı uygula: Django iskeleti, config/accounts/polls
uygulamaları, özel User modeli (bölüm 5.1), Supabase (pooler) uyumlu DATABASE_URL ayarları, Vercel uyumlu
wsgi/STATIC_ROOT ayarları, base.html + basit ana sayfa, .env.example, .gitignore ve README. Başka faza ait
hiçbir şey yazma. Bitince kabul kriterlerini kontrol et, elle yapmam gereken adımları listele ve dur.
```

---

## Faz 1 — Kullanıcı Sistemi (Kayıt, Giriş, Çıkış)

**Amaç:** Üye olma ve giriş yapma tam çalışsın; navbar duruma göre değişsin.

### Yapılacaklar

1. `accounts/forms.py`: `RegisterForm` (e-posta, kullanıcı adı, parola, parola tekrarı; bölüm 5.1 kuralları; benzersizlik kontrolü büyük/küçük harf duyarsız; Türkçe hata mesajları) ve `LoginForm` (tek alan: e-posta veya kullanıcı adı + parola).
2. `accounts/views.py` ve `urls.py`: `/kayit/`, `/giris/`, `/cikis/` (POST). Kayıt sonrası otomatik giriş + ana sayfaya yönlendirme. Giriş `?next=` parametresini güvenli şekilde desteklesin.
3. Giriş yapmış kullanıcı `/giris/` veya `/kayit/`'a gelirse ana sayfaya yönlendirilsin.
4. Şablonlar: `login.html`, `register.html` — tasarım rehberine uygun, mobil uyumlu, form hataları alan altında görünür.
5. Navbar'ı (bölüm 7) misafir/üye durumuna göre güncelle. `partials/messages.html` ile Django mesajlarını (başarı/hata) şık "toast" tarzında göster.
6. `/u/<username>/` profil sayfasını **şimdilik** yalnızca kullanıcı adı ve "Henüz anket yok" metniyle oluştur (anketler Faz 2'de eklenecek).
7. Django admin'de User modelini düzgün kaydet.

### Kabul kriterleri

- [ ] Geçerli bilgilerle kayıt olunabiliyor; aynı e-posta/kullanıcı adı (harf büyüklüğü fark etmeksizin) ikinci kez kullanılamıyor.
- [ ] Geçersiz kullanıcı adı (ör. boşluk, Türkçe karakter, 2 karakter) reddediliyor ve Türkçe mesaj veriliyor.
- [ ] Hem e-posta hem kullanıcı adıyla giriş yapılabiliyor.
- [ ] Çıkış çalışıyor; navbar duruma göre doğru gösteriliyor.
- [ ] Hiçbir sayfada e-posta görünmüyor.

### Prompt

```
kararsizim-plan.md dosyasını oku. Faz 0 tamamlandı. Sadece "Faz 1"i uygula: kayıt, giriş (e-posta veya
kullanıcı adı), çıkış, navbar'ın duruma göre değişmesi, mesaj/toast sistemi ve basit /u/<username>/ sayfası.
Tasarım rehberindeki (bölüm 8) renk ve bileşen stilini kullan. Anket ile ilgili hiçbir şey yazma. Bitince
kabul kriterlerini kontrol et ve dur.
```

---

## Faz 2 — Anket Oluşturma ve Listeleme

**Amaç:** Üyeler anket açabilsin; herkes anketleri listeleyip detayını görebilsin (henüz oy yok).

### Yapılacaklar

1. `Poll` ve `Option` modellerini (bölüm 5.2, 5.3) oluştur, migration'ları üret. `Vote` modelini de **şimdi** ekle (bölüm 5.4, kısıtlarıyla birlikte) ama oy verme mantığını Faz 3'e bırak.
2. `/anket/yeni/`: `login_required` (misafir → `/giris/?next=/anket/yeni/`, "Anket oluşturmak için önce giriş yapmalısın." mesajıyla). Form bölüm 7'deki kurallarla; `static/js/poll_form.js` ile dinamik seçenek ekleme/silme (2–5 sınırı) ve soru karakter sayacı. Sunucu tarafı doğrulaması + `transaction.atomic()`.
3. `/`: ana sayfa akışı (en yeni → en eski, sayfa başına 12, sayfalama), hero, anket kartı partial'ı (`partials/poll_card.html`), boş durum. N+1 sorgu olmasın (`select_related('author')`, `prefetch_related('options')`, toplam oy için `annotate`).
4. `/anket/<id>/`: detay sayfası — soru, yazar (@kullaniciadi), göreli zaman ("2 saat önce": Django `timesince` veya `naturaltime`), seçenekler **salt okunur** listelenir.
5. `/anket/<id>/sil/` (POST, yalnızca sahibi, yumuşak silme) + onay penceresi. Silinmiş anketler hiçbir listede/detayda görünmez (404).
6. `/u/<username>/` sayfasında kullanıcının anketlerini listele.
7. Admin'e Poll/Option/Vote'u ekle (Option inline).
8. `polls/tests.py`: anket oluşturma doğrulamaları (1 seçenek reddi, 6 seçenek reddi, tekrar eden seçenek reddi, misafirin oluşturamaması).

### Kabul kriterleri

- [ ] Misafir `/anket/yeni/`'ye gidince girişe yönlendiriliyor, giriş sonrası forma dönüyor.
- [ ] 2–5 dışındaki seçenek sayıları ve tekrar eden seçenekler sunucuda reddediliyor.
- [ ] Ana sayfa herkes için tüm anketleri gösteriyor; sayfalama çalışıyor.
- [ ] Başkasının anketini silme denemesi engelleniyor (403/404).
- [ ] Testler geçiyor.

### Prompt

```
kararsizim-plan.md dosyasını oku. Faz 0 ve 1 tamamlandı. Sadece "Faz 2"yi uygula: Poll/Option/Vote modelleri
(oy mantığı hariç), anket oluşturma formu (dinamik 2–5 seçenek, sunucu doğrulaması), ana sayfa akışı, kart
bileşeni, anket detay sayfası (salt okunur), silme, kullanıcı profil sayfasında anket listesi ve testler.
Oy verme ve sonuç gösterimini YAZMA. Bitince kabul kriterlerini kontrol et ve dur.
```

---

## Faz 3 — Oy Verme ve Sonuçlar

**Amaç:** Üyeler ve misafirler oy verebilsin; sonuçlar canlı güncellensin.

### Yapılacaklar

1. `polls/utils.py`: anonim token okuma/üretme, "bu istek için oy sahibi kim?" yardımcı fonksiyonu (giriş varsa user, yoksa cookie token), sonuç sözlüğü hesaplama (`options`, `votes`, `percent`, `total`, `my_option_id`).
2. `POST /anket/<id>/oy/` JSON ucu (bölüm 6): doğrulamalar, `update_or_create` ile tek oy / oy değiştirme, misafir için `kz_anon` cookie'sini cevapta set etme. Hata durumlarında bölüm 6'daki formatta Türkçe mesaj.
3. Detay sayfası (bölüm 7): oy vermemiş için gizli sonuçlar + "Oy vermeden sonuçları gör"; oy vermiş için (sayfa yenilenince de) yüzde çubukları + ✓ vurgusu + toplam oy. `@ensure_csrf_cookie`.
4. `static/js/vote.js`: seçeneğe tıklayınca `fetch` ile oy gönder, sayfayı yenilemeden çubukları animasyonla güncelle, hata olursa toast göster, çift tıklamayı engelle (istek sürerken butonlar devre dışı). DOM'a kullanıcı metni `textContent` ile yazılsın.
5. Ana sayfa/profil kartlarında toplam oy sayısını göster.
6. Testler: misafir oyu, üye oyu, oy değiştirme (kayıt sayısı artmıyor), başka anketin seçeneğiyle oy verme reddi, silinmiş ankete oy reddi, bir kişinin iki oyu olamaması, JSON cevabında e-posta bulunmaması.

### Kabul kriterleri

- [ ] Giriş yapmadan oy verilebiliyor; sayfa yenilenince oy hatırlanıyor.
- [ ] Üye oy veriyor; farklı tarayıcıda aynı hesapla girince oyu görüyor.
- [ ] Aynı kişi aynı ankette ikinci kayıt oluşturamıyor, sadece oyunu değiştirebiliyor.
- [ ] Yüzdeler doğru; hiç oy yokken bölme hatası yok.
- [ ] Testler geçiyor.

### Prompt

```
kararsizim-plan.md dosyasını oku. Faz 0, 1 ve 2 tamamlandı. Sadece "Faz 3"ü uygula: oy verme JSON ucu
(üye + anonim cookie token), tek oy/oy değiştirme, sonuç hesaplama, detay sayfasında oy öncesi/sonrası
görünümler, vote.js ile sayfa yenilemeden güncelleme ve testler. IP veya parmak izi gibi takip yöntemi
KULLANMA. Bitince kabul kriterlerini kontrol et ve dur.
```

---

## Faz 4 — Arayüz Cilası, Hatalar ve Yayına Hazırlık

**Amaç:** Prototipi arkadaşlara gösterilebilir kalitede toparlamak.

### Yapılacaklar

1. Tasarımı bölüm 8'e göre gözden geçir ve cilala: hero dekorları, kart hover'ları, çubuk animasyonları, buton/form stilleri, seçenek renk döngüsü, `prefers-reduced-motion`.
2. 360px, 768px, 1280px genişliklerinde tüm sayfaları kontrol et ve düzelt.
3. Özel `404.html` ve `500.html`; boş durumlar; yükleniyor/hata durumları.
4. `<title>`, `<meta description>`, Open Graph temel etiketleri (anket detayında soru başlık olsun), favicon (emoji tabanlı SVG yeterli).
5. Güvenlik kontrolü: bölüm 9'daki maddeleri tek tek doğrula; `DEBUG=False` ile production ayarlarını (secure cookie, `CSRF_TRUSTED_ORIGINS`) test et.
6. Basit bir "Nasıl çalışır?" alanı veya kısa bilgi bölümü (ana sayfada 3 adım: Sor → Paylaş → Oyla).
7. README'yi güncelle: kurulum, ortam değişkenleri, deploy adımları, bilinen sınırlamalar (cookie silinirse tekrar oy verilebilir).

### Kabul kriterleri

- [ ] Mobilde ve masaüstünde tüm sayfalar düzgün görünüyor.
- [ ] Production modunda (DEBUG=False) tüm akışlar çalışıyor.
- [ ] Vercel'deki canlı sürümde kayıt → anket oluştur → misafir olarak oy ver akışı baştan sona çalışıyor.

### Prompt

```
kararsizim-plan.md dosyasını oku. Faz 0–3 tamamlandı. Sadece "Faz 4"ü uygula: arayüz cilası, responsive
kontrolleri, 404/500 sayfaları, meta etiketleri, güvenlik/production kontrolleri ve README güncellemesi.
Yeni özellik ekleme. Bitince kabul kriterlerini ve bölüm 9'daki güvenlik maddelerini tek tek kontrol edip
raporla ve dur.
```

---

## Faz 5 — Sonraki Adımlar (Backlog, şimdi YAPMA)

Prototip onaylandıktan sonra, öncelik sırasıyla düşünülebilecekler:

1. E-posta doğrulama ve şifre sıfırlama (Supabase SMTP veya Resend gibi bir servis).
2. Basit hız sınırlama (oy ve anket oluşturma için) ve spam/küfür filtresi, "Şikâyet et" butonu.
3. Anketi kapatma / bitiş süresi koyma.
4. Anket paylaşım bağlantısı ve "Kopyala" butonu; sosyal medya önizleme görseli.
5. Sıralama seçenekleri (Yeni / En çok oylanan / Bugün) ve arama.
6. Kategoriler veya etiketler.
7. Karanlık mod.
8. Yorum özelliği.
9. Anonim oyların üye olunca hesaba bağlanması.
10. Gerçek zamanlı sonuç güncelleme (polling veya Supabase Realtime).
