import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from config.throttling import get_client_ip, is_rate_limited
from .forms import PollCreateForm
from .models import Option, Poll, Vote
from .utils import (
    ANON_COOKIE_MAX_AGE,
    ANON_COOKIE_NAME,
    calculate_poll_results,
    generate_anon_token,
    get_anon_token,
    get_user_vote_option_id,
)

POLLS_PER_PAGE = 12


def home(request):
    """Ana sayfa: en yeni anketler, sayfa başına 12 + QuestionPro tarzı yan panel verileri."""
    base_qs = (
        Poll.objects
        .filter(is_active=True)
        .select_related('author')
        .prefetch_related('options')
        .annotate(total_votes=Count('votes'))
    )
    polls_qs = base_qs.order_by('-created_at')
    paginator = Paginator(polls_qs, POLLS_PER_PAGE)
    page_number = request.GET.get('sayfa', 1)
    page_obj = paginator.get_page(page_number)

    # Yan panel: Popüler anketler ve istatistikler
    popular_polls = base_qs.order_by('-total_votes', '-created_at')[:4]
    total_polls_count = Poll.objects.filter(is_active=True).count()
    total_votes_count = Vote.objects.count()

    return render(request, 'polls/home.html', {
        'page_obj': page_obj,
        'popular_polls': popular_polls,
        'total_polls_count': total_polls_count,
        'total_votes_count': total_votes_count,
    })


def poll_create(request):
    """Anket oluşturma sayfası — yalnızca giriş yapmış kullanıcılar."""
    if not request.user.is_authenticated:
        messages.info(request, 'Anket oluşturmak için önce giriş yapmalısın.')
        return redirect(f'{settings.LOGIN_URL}?next={request.path}')

    submitted_options = ['', '']

    if request.method == 'POST':
        form = PollCreateForm(request.POST)
        raw_options = [request.POST.get(f'option_{i}', '').strip() for i in range(5)]
        non_empty = [opt for opt in raw_options if opt]
        submitted_options = non_empty if len(non_empty) >= 2 else (non_empty + [''] * (2 - len(non_empty)))

        if form.is_valid():
            question = form.cleaned_data['question']
            options = form.cleaned_data['options']
            with transaction.atomic():
                poll = Poll.objects.create(
                    author=request.user,
                    question=question
                )
                for position, text in enumerate(options):
                    Option.objects.create(
                        poll=poll,
                        text=text,
                        position=position
                    )
            messages.success(request, 'Anketin yayında! 🎉')
            return redirect('polls:detail', pk=poll.pk)
    else:
        form = PollCreateForm()

    return render(request, 'polls/create.html', {
        'form': form,
        'submitted_options': submitted_options,
    })


@ensure_csrf_cookie
def poll_detail(request, pk):
    """Anket detay sayfası — oy verme ve sonuç görünümü."""
    poll = get_object_or_404(
        Poll.objects.select_related('author').prefetch_related('options'),
        pk=pk,
        is_active=True
    )
    my_option_id = get_user_vote_option_id(poll, request)
    results = calculate_poll_results(poll, my_option_id=my_option_id)

    return render(request, 'polls/detail.html', {
        'poll': poll,
        'my_option_id': my_option_id,
        'results': results,
    })


@require_POST
def poll_vote(request, pk):
    """JSON oy verme uç noktası (üye ve misafir)."""
    # Hız sınırlama denetimi (IP bazlı - bot ve kaba kuvvet spamini engeller)
    client_ip = get_client_ip(request)
    limited, retry_after = is_rate_limited('vote', client_ip, limit=20, period=60)
    if limited:
        return JsonResponse(
            {'ok': False, 'error': f'Çok hızlı oy kullanıyorsunuz. Lütfen {retry_after} saniye bekleyin.'},
            status=429
        )

    poll = Poll.objects.filter(pk=pk, is_active=True).first()
    if poll is None:
        return JsonResponse(
            {'ok': False, 'error': 'Anket bulunamadı veya silinmiş.'},
            status=404
        )

    try:
        data = json.loads(request.body.decode('utf-8'))
        # Bot koruması (honeypot alanı doluysa reddet)
        if data.get('website') or data.get('hp_field'):
            return JsonResponse({'ok': False, 'error': 'İstek reddedildi.'}, status=400)

        option_id = int(data.get('option_id'))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse(
            {'ok': False, 'error': 'Geçersiz oy verisi.'},
            status=400
        )

    option = Option.objects.filter(pk=option_id, poll=poll).first()
    if option is None:
        return JsonResponse(
            {'ok': False, 'error': 'Seçilen seçenek bu ankete ait değil.'},
            status=400
        )

    new_anon_token = None
    if request.user.is_authenticated:
        Vote.objects.update_or_create(
            poll=poll,
            user=request.user,
            defaults={'option': option, 'anon_token': None}
        )
    else:
        token = get_anon_token(request)
        if not token:
            token = generate_anon_token()
            new_anon_token = token
        Vote.objects.update_or_create(
            poll=poll,
            anon_token=token,
            defaults={'option': option, 'user': None}
        )

    results = calculate_poll_results(poll, my_option_id=option.id)
    response = JsonResponse(results, status=200)

    if new_anon_token:
        response.set_cookie(
            ANON_COOKIE_NAME,
            new_anon_token,
            max_age=ANON_COOKIE_MAX_AGE,
            httponly=True,
            samesite='Lax',
            secure=not settings.DEBUG,
        )

    return response


@require_POST
@login_required
def poll_delete(request, pk):
    """Anketi sil (yumuşak silme) — yalnızca anketin sahibi."""
    poll = get_object_or_404(Poll, pk=pk, is_active=True)
    if poll.author != request.user:
        raise Http404
    poll.is_active = False
    poll.save(update_fields=['is_active'])
    messages.success(request, 'Anket silindi.')
    return redirect('polls:home')
