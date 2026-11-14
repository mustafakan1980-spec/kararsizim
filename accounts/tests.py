from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.home_url = reverse('polls:home')

        # Test için mevcut bir kullanıcı oluştur
        self.existing_user = User.objects.create_user(
            username='mevcut_kullanici',
            email='mevcut@example.com',
            password='Password123!'
        )

    def test_register_success(self):
        """Geçerli bilgilerle kayıt olunabilmeli ve kullanıcı oturumu açılmalı."""
        data = {
            'username': 'Yeni_Kullanici',
            'email': 'YENI@example.com',
            'password': 'GucluParola123!',
            'password_confirm': 'GucluParola123!'
        }
        response = self.client.post(self.register_url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Kullanıcı veritabanında küçük harfle kayıt edilmiş olmalı
        user = User.objects.get(username='yeni_kullanici')
        self.assertEqual(user.email, 'yeni@example.com')

        # Oturum açık olmalı
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'yeni_kullanici')

    def test_register_duplicate_username_case_insensitive(self):
        """Aynı kullanıcı adı büyük/küçük harf fark etmeksizin reddedilmeli."""
        data = {
            'username': 'MEVCUT_KULLANICI',
            'email': 'farkli@example.com',
            'password': 'GucluParola123!',
            'password_confirm': 'GucluParola123!'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'username', 'Bu kullanıcı adı zaten kullanılıyor.')

    def test_register_duplicate_email_case_insensitive(self):
        """Aynı e-posta büyük/küçük harf fark etmeksizin reddedilmeli."""
        data = {
            'username': 'baskasi',
            'email': 'MEVCUT@example.com',
            'password': 'GucluParola123!',
            'password_confirm': 'GucluParola123!'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'email', 'Bu e-posta adresi zaten kayıtlı.')

    def test_register_invalid_username_characters(self):
        """Türkçe karakter, boşluk veya özel karakter içeren kullanıcı adı reddedilmeli."""
        invalid_usernames = ['ali veli', 'kullanıcı', 'test@user', 'ab', 'a' * 21]
        for uname in invalid_usernames:
            data = {
                'username': uname,
                'email': f'{uname.replace(" ", "_")}@example.com',
                'password': 'GucluParola123!',
                'password_confirm': 'GucluParola123!'
            }
            response = self.client.post(self.register_url, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].errors.get('username'))

    def test_register_password_mismatch(self):
        """Parolalar eşleşmediğinde hata verilmeli."""
        data = {
            'username': 'uyumsuz',
            'email': 'uyumsuz@example.com',
            'password': 'GucluParola123!',
            'password_confirm': 'FarkliParola123!'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'password_confirm', 'Parolalar eşleşmiyor.')

    def test_login_with_username(self):
        """Kullanıcı adı ile giriş yapılabilmeli."""
        response = self.client.post(self.login_url, {
            'login': 'mevcut_kullanici',
            'password': 'Password123!'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'mevcut_kullanici')

    def test_login_with_email(self):
        """E-posta adresi ile giriş yapılabilmeli."""
        response = self.client.post(self.login_url, {
            'login': 'MEVCUT@EXAMPLE.COM',
            'password': 'Password123!'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'mevcut_kullanici')

    def test_login_invalid_credentials(self):
        """Hatalı parola reddedilmeli."""
        response = self.client.post(self.login_url, {
            'login': 'mevcut_kullanici',
            'password': 'YanlisParola!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())

    def test_login_with_safe_next_url(self):
        """Güvenli next URL yönlendirmesi çalışmalı."""
        next_target = reverse('accounts:profile', kwargs={'username': 'mevcut_kullanici'})
        response = self.client.post(f"{self.login_url}?next={next_target}", {
            'login': 'mevcut_kullanici',
            'password': 'Password123!'
        })
        self.assertRedirects(response, next_target)

    def test_login_with_unsafe_next_url(self):
        """Güvensiz harici next URL ana sayfaya yönlendirilmeli."""
        response = self.client.post(f"{self.login_url}?next=https://hacker.com/steal", {
            'login': 'mevcut_kullanici',
            'password': 'Password123!'
        })
        self.assertRedirects(response, self.home_url)

    def test_authenticated_user_redirected_from_login_and_register(self):
        """Giriş yapmış kullanıcı /giris/ veya /kayit/ adresine gittiğinde ana sayfaya yönlendirilmeli."""
        self.client.force_login(self.existing_user)

        response_login = self.client.get(self.login_url)
        self.assertRedirects(response_login, self.home_url)

        response_register = self.client.get(self.register_url)
        self.assertRedirects(response_register, self.home_url)

    def test_logout(self):
        """Çıkış POST isteği ile çalışmalı."""
        self.client.force_login(self.existing_user)
        response = self.client.post(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_profile_page_does_not_leak_email(self):
        """Profil sayfasında kullanıcı adı görünmeli fakat e-posta ASLA görünmemeli."""
        profile_url = reverse('accounts:profile', kwargs={'username': 'mevcut_kullanici'})
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn('@mevcut_kullanici', content)
        self.assertNotIn('mevcut@example.com', content)
        self.assertNotIn('@example.com', content)

    def test_security_headers_present(self):
        """CSP ve modern güvenlik başlıkları yanıtta bulunmalı."""
        response = self.client.get(self.login_url)
        self.assertIn('Content-Security-Policy', response.headers)
        self.assertIn('Permissions-Policy', response.headers)
        self.assertIn('Cross-Origin-Opener-Policy', response.headers)
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')

    def test_login_rate_limiting(self):
        """Aşırı sayıda ardışık giriş denemesi 429 Hız Sınırı Aşıldı döndürmeli."""
        from django.core.cache import cache
        cache.clear()

        # 10 deneme limiti tanımlandı
        for _ in range(10):
            self.client.post(self.login_url, {
                'login': 'yanlis_kullanici',
                'password': 'YanlisSifre!'
            })
        blocked_response = self.client.post(self.login_url, {
            'login': 'yanlis_kullanici',
            'password': 'YanlisSifre!'
        })
        self.assertEqual(blocked_response.status_code, 429)
        cache.clear()
