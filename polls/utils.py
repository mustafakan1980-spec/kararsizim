import uuid
from django.db.models import Count

from .models import Vote

ANON_COOKIE_NAME = 'kz_anon'
ANON_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 yıl


def get_anon_token(request):
    """İstek çerezinden anonim oy token'ını okur."""
    token = request.COOKIES.get(ANON_COOKIE_NAME, '').strip()
    if token and len(token) <= 64:
        return token
    return None


def generate_anon_token():
    """Yeni bir rastgele anonim oy token'ı üretir."""
    return uuid.uuid4().hex


def get_user_vote_option_id(poll, request):
    """Mevcut kullanıcının (üye veya anonim) bu ankette verdiği oy seçeneğinin ID'sini döndürür."""
    if request.user.is_authenticated:
        return (
            Vote.objects
            .filter(poll=poll, user=request.user)
            .values_list('option_id', flat=True)
            .first()
        )

    token = get_anon_token(request)
    if token:
        return (
            Vote.objects
            .filter(poll=poll, anon_token=token)
            .values_list('option_id', flat=True)
            .first()
        )
    return None


def calculate_poll_results(poll, my_option_id=None):
    """Anket seçeneklerinin oy sayılarını ve yüzdelerini hesaplar."""
    options_qs = poll.options.annotate(vote_count=Count('votes')).order_by('position')
    options_list = list(options_qs)
    total = sum(opt.vote_count for opt in options_list)

    options_data = []
    for opt in options_list:
        percent = round(opt.vote_count / total * 100) if total > 0 else 0
        options_data.append({
            'id': opt.id,
            'text': opt.text,
            'votes': opt.vote_count,
            'percent': percent,
        })

    return {
        'ok': True,
        'my_option_id': my_option_id,
        'total': total,
        'options': options_data,
    }
