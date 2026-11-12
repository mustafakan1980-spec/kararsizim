from django.shortcuts import render


def home(request):
    """Ana sayfa görünümü (Faz 0 başlangıcı)."""
    return render(request, 'polls/home.html')
