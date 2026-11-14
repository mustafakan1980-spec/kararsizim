---
name: web-guvenlik-kontrolu
description: Web sitelerinin güvenlik açıklarını (OWASP Top 10, XSS, SQLi, CSRF vb.) analiz eder ve zafiyet tarama raporu oluşturur. Güvenlik testleri, pentest veya kod güvenliği incelemesi istendiğinde kullanılır.
---

# Web Sitesi Güvenlik ve Zafiyet Kontrolü

Bu yetenek, web uygulamalarının güvenlik açıklarını tespit etmek, OWASP standartlarına uygunluk denetimi yapmak ve güvenli kodlama pratiklerini denetlemek için kullanılır.

## 1. Temel Kontrol Alanları (OWASP Top 10 Odaklı)
Güvenlik incelemesi sırasında şu kritik başlıklar taranır:
- **Enjeksiyon Zafiyetleri:** SQL Injection (SQLi), Command Injection.
- **Kimlik Doğrulama ve Oturum Yönetimi:** Zayıf şifre politikaları, güvensiz oturum açma (Session Fixation).
- **Hassas Veri İfşası:** Şifrelenmemiş hassas veriler (HTTP üzerinden şifresiz veri aktarımı, açıkta kalan API anahtarları).
- **XSS (Cross-Site Scripting):** Saklı (Stored), Yansıtılmış (Reflected) ve DOM tabanlı XSS açıklarının tespiti.
- **CSRF (Cross-Site Request Forgery):** Eksik veya zayıf Anti-CSRF token korumaları.
- **Güvenlik Başlıkları (Security Headers):** `Content-Security-Policy (CSP)`, `X-Frame-Options`, `Strict-Transport-Security (HSTS)` eksiklikleri.

## 2. Güvenlik Denetim Adımları

1. **Keşif ve Bilgi Toplama (Reconnaissance):**
   - Hedef uygulamanın teknolojilerini (kullanılan framework, sunucu tipi) tespit edin.
   - Açıkta kalmış hassas dosya ve dizinleri (`/robots.txt`, `.git/`, `/.env`, yedek dosyalar) kontrol edin.
   *Verification:* Uygulamanın dışarıya sızdırdığı gereksiz sürüm bilgileri veya yapılandırma dosyaları listelenir.

2. **Statik Kod Analizi (SAST) veya Kod İncelemesi:**
   - Kod tabanında kullanıcıdan gelen verilerin (input) doğrudan veritabanına veya HTML çıktısına gidip gitmediğini inceleyin.
   - Güvensiz fonksiyonların (`eval()`, doğrudan SQL sorgu birleştirmeleri vb.) kullanımını arayın.

3. **Dinamik Girdi Testleri (DAST / Simülasyon):**
   - Form alanlarına, URL parametrelerine ve API uç noktalarına özel karakterler (`' OR '1'='1`, `<script>alert(1)</script>`) göndererek uygulamanın tepkisini gözlemleyin.
   *Verification:* Uygulamanın hataları ekrana (stack trace olarak) yansıtıp yansıtmadığını veya girdileri filtreleyip filtrelemediğini doğrulayın.

4. **HTTP Güvenlik Başlıkları Kontrolü:**
   - Yanıt başlıklarında koruyucu header'ların olup olmadığını inceleyin.

## 3. Güvenlik Raporlama Formatı
Tespit edilen açıklar şu şablona göre raporlanır:
- **Zafiyet Adı:** (Örn: SQL Injection / XSS)
- **Risk Seviyesi:** (Kritik / Yüksek / Orta / Düşük)
- **Konulduk Yeri / Uç Nokta:** (Hangi sayfa veya API rotası)
- **Çözüm / Düzeltme Önerisi:** (Güvenli kod örneği veya alınması gereken önlem)

## ⚠️ Kritik Yasal Uyarı
> **Yasal Uyarı:** Güvenlik taramaları ve testleri yalnızca **sahibi olduğunuz** veya üzerinde açık ve yazılı **test izni bulunan** sistemler üzerinde gerçekleştirilmelidir. Yetkisiz hedef taramaları yasal suç teşkil eder.
