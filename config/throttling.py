"""
Hız Sınırlama (Rate Limiting / Throttling) Yardımcıları.
Kaba kuvvet (brute-force) ve bot saldırılarını önlemek için IP ve işlem bazlı hız sınırlaması sağlar.
"""

import time
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib import messages


def get_client_ip(request):
    """İstekten istemci IP adresini güvenli şekilde çıkarır."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip or '127.0.0.1'


def is_rate_limited(action_name, identifier, limit=5, period=60):
    """
    Belirli bir işlem ve tanımlayıcı (IP veya kullanıcı adı) için hız sınırını denetler.

    :param action_name: 'login', 'register', 'vote' gibi işlem adı
    :param identifier: İstemci IP adresi veya kullanıcı adı
    :param limit: Belirtilen periyotta izin verilen azami istek sayısı
    :param period: Saniye cinsinden zaman penceresi
    :return: (is_limited: bool, retry_after: int)
    """
    cache_key = f"rl:{action_name}:{identifier}"
    now = int(time.time())

    history = cache.get(cache_key) or []
    # Zaman penceresi dışındaki eski kayıtları temizle
    history = [t for t in history if t > now - period]

    if len(history) >= limit:
        oldest = history[0]
        retry_after = max(1, (oldest + period) - now)
        return True, retry_after

    history.append(now)
    cache.set(cache_key, history, timeout=period + 5)
    return False, 0
