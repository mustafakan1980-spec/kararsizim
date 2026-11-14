"""
Güvenlik Başlıkları (Security Headers) ve CSP Middleware'i.
Tüm HTTP yanıtlarına modern güvenlik başlıklarını ekler.
"""


class SecurityHeadersMiddleware:
    """Tüm yanıtlara CSP ve ek güvenlik başlıkları ekleyen ara yazılım."""

    CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "base-uri 'self';"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Content Security Policy (XSS ve yetkisiz kaynak yüklemelerini önler)
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = self.CSP_POLICY

        # Permissions-Policy (Tarayıcı donanım erişim kısıtlamaları)
        if 'Permissions-Policy' not in response:
            response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=()'

        # Cross-Origin-Opener-Policy
        if 'Cross-Origin-Opener-Policy' not in response:
            response['Cross-Origin-Opener-Policy'] = 'same-origin'

        # MIME sniffing koruması
        if 'X-Content-Type-Options' not in response:
            response['X-Content-Type-Options'] = 'nosniff'

        return response
