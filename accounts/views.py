from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from config.throttling import get_client_ip, is_rate_limited
from .forms import LoginForm, RegisterForm

User = get_user_model()


def register_view(request):
    """Yeni kullanıcı kaydı."""
    if request.user.is_authenticated:
        return redirect('polls:home')

    if request.method == 'POST':
        ip = get_client_ip(request)
        limited, retry_after = is_rate_limited('register', ip, limit=5, period=60)
        if limited:
            messages.error(
                request,
                f'Çok fazla kayıt denemesi yapıldı. Lütfen {retry_after} saniye sonra tekrar deneyin.'
            )
            return render(request, 'accounts/register.html', {'form': RegisterForm(request.POST)}, status=429)

        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Aramıza hoş geldin, @{user.username}! 🎉')
            return redirect('polls:home')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Kullanıcı girişi (e-posta veya kullanıcı adı ile)."""
    if request.user.is_authenticated:
        return redirect('polls:home')

    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        ip = get_client_ip(request)
        limited, retry_after = is_rate_limited('login', ip, limit=10, period=60)
        if limited:
            messages.error(
                request,
                f'Çok fazla giriş denemesi yapıldı. Lütfen {retry_after} saniye sonra tekrar deneyin.'
            )
            return render(request, 'accounts/login.html', {
                'form': LoginForm(request.POST),
                'next': next_url,
            }, status=429)

        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Tekrar hoş geldin, @{user.username}! 👋')

            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure()
            ):
                return redirect(next_url)
            return redirect('polls:home')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'next': next_url,
    })


@require_POST
def logout_view(request):
    """Kullanıcı çıkışı (yalnızca POST ile kabul edilir)."""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'Başarıyla çıkış yapıldı. Görüşmek üzere! 👋')
    return redirect('polls:home')


def profile_view(request, username):
    """Kullanıcı profil sayfası (e-posta asla gösterilmez)."""
    profile_user = get_object_or_404(User, username__iexact=username)
    polls = (
        profile_user.polls
        .filter(is_active=True)
        .prefetch_related('options')
        .annotate(total_votes=Count('votes'))
        .order_by('-created_at')
    )
    return render(request, 'accounts/profile.html', {
        'profile_user': profile_user,
        'polls': polls,
    })
