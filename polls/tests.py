from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Option, Poll

User = get_user_model()


class PollsFaz2Tests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='kullanici1',
            email='user1@example.com',
            password='Password123!'
        )
        self.user2 = User.objects.create_user(
            username='kullanici2',
            email='user2@example.com',
            password='Password123!'
        )
        self.create_url = reverse('polls:create')
        self.home_url = reverse('polls:home')
        self.login_url = reverse('accounts:login')

    def test_guest_cannot_access_poll_create(self):
        """Misafir anket oluşturma sayfasına girince girişe yönlendirilmeli."""
        response = self.client.get(self.create_url)
        self.assertRedirects(response, f'{self.login_url}?next={self.create_url}')

        response_post = self.client.post(self.create_url, {
            'question': 'Test soru?',
            'option_0': 'A',
            'option_1': 'B',
        })
        self.assertRedirects(response_post, f'{self.login_url}?next={self.create_url}')
        self.assertEqual(Poll.objects.count(), 0)

    def test_create_poll_success(self):
        """Giriş yapmış kullanıcı 2-5 seçenekle anket oluşturabilmeli."""
        self.client.force_login(self.user1)
        response = self.client.post(self.create_url, {
            'question': 'Akşama ne yiyelim?',
            'option_0': 'Pizza',
            'option_1': 'Burger',
            'option_2': 'Döner',
        })
        self.assertEqual(Poll.objects.count(), 1)
        poll = Poll.objects.first()
        self.assertEqual(poll.question, 'Akşama ne yiyelim?')
        self.assertEqual(poll.author, self.user1)
        self.assertEqual(poll.options.count(), 3)
        self.assertEqual(list(poll.options.values_list('text', flat=True)), ['Pizza', 'Burger', 'Döner'])
        self.assertRedirects(response, reverse('polls:detail', kwargs={'pk': poll.pk}))

    def test_create_poll_reject_single_option(self):
        """1 seçenekli anket reddedilmeli."""
        self.client.force_login(self.user1)
        response = self.client.post(self.create_url, {
            'question': 'Tek seçenek?',
            'option_0': 'Sadece bu',
            'option_1': '   ',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Poll.objects.count(), 0)
        self.assertIn('En az 2 seçenek girmelisiniz.', response.context['form'].non_field_errors())

    def test_create_poll_reject_six_options(self):
        """6 seçenekli anket reddedilmeli."""
        self.client.force_login(self.user1)
        response = self.client.post(self.create_url, {
            'question': 'Çok seçenek?',
            'option_0': 'Bir',
            'option_1': 'İki',
            'option_2': 'Üç',
            'option_3': 'Dört',
            'option_4': 'Beş',
            'option_5': 'Altı',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Poll.objects.count(), 0)
        self.assertIn('En fazla 5 seçenek girebilirsiniz.', response.context['form'].non_field_errors())

    def test_create_poll_reject_duplicate_options_case_insensitive(self):
        """Büyük/küçük harf duyarsız tekrar eden seçenekler reddedilmeli."""
        self.client.force_login(self.user1)
        response = self.client.post(self.create_url, {
            'question': 'Tekrar eden?',
            'option_0': 'Sinema',
            'option_1': 'sinema',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Poll.objects.count(), 0)
        self.assertIn('Seçenekler birbirinin aynısı olamaz.', response.context['form'].non_field_errors())

    def test_home_page_listing_and_pagination(self):
        """Ana sayfa en yeni anketleri 12'li sayfalar halinde listelemeli."""
        for i in range(15):
            p = Poll.objects.create(author=self.user1, question=f'Soru {i}')
            Option.objects.create(poll=p, text='Evet', position=0)
            Option.objects.create(poll=p, text='Hayır', position=1)

        response1 = self.client.get(self.home_url)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(len(response1.context['page_obj']), 12)

        response2 = self.client.get(f'{self.home_url}?sayfa=2')
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(len(response2.context['page_obj']), 3)

    def test_poll_detail_and_soft_delete(self):
        """Anket sahibi anketini silebilmeli; başkası silememeli; silinen anket 404 vermeli."""
        poll = Poll.objects.create(author=self.user1, question='Silinecek anket?')
        Option.objects.create(poll=poll, text='A', position=0)
        Option.objects.create(poll=poll, text='B', position=1)

        detail_url = reverse('polls:detail', kwargs={'pk': poll.pk})
        delete_url = reverse('polls:delete', kwargs={'pk': poll.pk})

        # Başkası silemez
        self.client.force_login(self.user2)
        res_other = self.client.post(delete_url)
        self.assertEqual(res_other.status_code, 404)
        poll.refresh_from_db()
        self.assertTrue(poll.is_active)

        # Sahibi silebilir
        self.client.force_login(self.user1)
        res_owner = self.client.post(delete_url)
        self.assertRedirects(res_owner, self.home_url)
        poll.refresh_from_db()
        self.assertFalse(poll.is_active)

        # Silinen anket detayda 404 verir, ana sayfada ve profilde görünmez
        res_detail = self.client.get(detail_url)
        self.assertEqual(res_detail.status_code, 404)

        res_home = self.client.get(self.home_url)
        self.assertNotContains(res_home, 'Silinecek anket?')

        res_profile = self.client.get(reverse('accounts:profile', kwargs={'username': 'kullanici1'}))
        self.assertNotContains(res_profile, 'Silinecek anket?')


class PollsFaz3VoteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='oyveren',
            email='oyveren@example.com',
            password='Password123!'
        )
        self.poll = Poll.objects.create(author=self.user, question='Sinema mı Restoran mı?')
        self.opt1 = Option.objects.create(poll=self.poll, text='Sinema', position=0)
        self.opt2 = Option.objects.create(poll=self.poll, text='Restoran', position=1)

        self.other_poll = Poll.objects.create(author=self.user, question='Başka anket?')
        self.other_opt = Option.objects.create(poll=self.other_poll, text='Evet', position=0)

        self.vote_url = reverse('polls:vote', kwargs={'pk': self.poll.pk})
        self.detail_url = reverse('polls:detail', kwargs={'pk': self.poll.pk})

    def test_guest_vote_sets_cookie_and_remembers_on_reload(self):
        """Misafir oy verebilmeli, kz_anon cookie set edilmeli ve sayfa yenilenince hatırlanmalı."""
        response = self.client.post(
            self.vote_url,
            data={'option_id': self.opt1.pk},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['my_option_id'], self.opt1.pk)
        self.assertEqual(data['total'], 1)

        # kz_anon cookie set edilmiş olmalı
        self.assertIn('kz_anon', response.cookies)
        self.assertTrue(response.cookies['kz_anon']['httponly'])

        # Sayfa yenilenince oy hatırlanmalı
        detail_res = self.client.get(self.detail_url)
        self.assertEqual(detail_res.status_code, 200)
        self.assertEqual(detail_res.context['my_option_id'], self.opt1.pk)

    def test_member_vote_and_change_vote_keeps_single_record(self):
        """Üye oy verebilmeli ve oyunu değiştirdiğinde ikinci kayıt oluşmamalı."""
        from .models import Vote
        self.client.force_login(self.user)

        # İlk oy
        res1 = self.client.post(
            self.vote_url,
            data={'option_id': self.opt1.pk},
            content_type='application/json'
        )
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(Vote.objects.filter(poll=self.poll, user=self.user).count(), 1)

        # Oy değiştirme
        res2 = self.client.post(
            self.vote_url,
            data={'option_id': self.opt2.pk},
            content_type='application/json'
        )
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2['my_option_id'], self.opt2.pk)
        self.assertEqual(data2['total'], 1)
        self.assertEqual(Vote.objects.filter(poll=self.poll, user=self.user).count(), 1)

        # Yüzdeler doğru olmalı (opt1: 0%, opt2: 100%)
        opts_by_id = {o['id']: o for o in data2['options']}
        self.assertEqual(opts_by_id[self.opt1.pk]['percent'], 0)
        self.assertEqual(opts_by_id[self.opt2.pk]['percent'], 100)

    def test_guest_change_vote_keeps_single_record(self):
        """Misafir oyunu değiştirdiğinde yeni kayıt açılmamalı."""
        from .models import Vote
        self.client.post(
            self.vote_url,
            data={'option_id': self.opt1.pk},
            content_type='application/json'
        )
        res2 = self.client.post(
            self.vote_url,
            data={'option_id': self.opt2.pk},
            content_type='application/json'
        )
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(Vote.objects.filter(poll=self.poll).count(), 1)
        self.assertEqual(res2.json()['my_option_id'], self.opt2.pk)

    def test_vote_with_other_poll_option_rejected(self):
        """Başka anketin seçeneğiyle oy verme 400 ile reddedilmeli."""
        response = self.client.post(
            self.vote_url,
            data={'option_id': self.other_opt.pk},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])

    def test_vote_on_deleted_poll_rejected(self):
        """Silinmiş ankete oy verme 404 ile reddedilmeli."""
        self.poll.is_active = False
        self.poll.save(update_fields=['is_active'])
        response = self.client.post(
            self.vote_url,
            data={'option_id': self.opt1.pk},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()['ok'])

    def test_zero_votes_no_division_error_and_no_email_in_json(self):
        """Hiç oy yokken bölme hatası olmamalı ve JSON cevabında e-posta bulunmamalı."""
        from .utils import calculate_poll_results
        res = calculate_poll_results(self.poll)
        self.assertEqual(res['total'], 0)
        for o in res['options']:
            self.assertEqual(o['percent'], 0)

        vote_res = self.client.post(
            self.vote_url,
            data={'option_id': self.opt1.pk},
            content_type='application/json'
        )
        raw_json = vote_res.content.decode('utf-8')
        self.assertNotIn('oyveren@example.com', raw_json)
        self.assertNotIn('@example.com', raw_json)
