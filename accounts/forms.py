import re
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q

User = get_user_model()


class RegisterForm(forms.Form):
    username = forms.CharField(
        label='Kullanıcı Adı',
        max_length=20,
        min_length=3,
        widget=forms.TextInput(attrs={
            'placeholder': 'ornek_kullanici',
            'class': 'form-input',
            'autocomplete': 'username',
            'autofocus': True,
        }),
        help_text='3–20 karakter, yalnızca harf (a-z), rakam ve alt çizgi (_).'
    )
    email = forms.EmailField(
        label='E-posta',
        widget=forms.EmailInput(attrs={
            'placeholder': 'ornek@eposta.com',
            'class': 'form-input',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        label='Parola',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'En az 8 karakter',
            'class': 'form-input',
            'autocomplete': 'new-password',
        })
    )
    password_confirm = forms.CharField(
        label='Parola Tekrarı',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Parolanızı tekrar girin',
            'class': 'form-input',
            'autocomplete': 'new-password',
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        # Sadece İngilizce harfler (a-z, A-Z), rakamlar ve alt çizgi
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            raise forms.ValidationError(
                'Kullanıcı adı 3–20 karakter olmalı ve yalnızca harf (a-z), rakam ve alt çizgi (_) içermelidir.'
            )
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Bu kullanıcı adı zaten kullanılıyor.')
        return username.lower()

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError('E-posta alanı zorunludur.')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Bu e-posta adresi zaten kayıtlı.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', 'Parolalar eşleşmiyor.')
            else:
                try:
                    validate_password(password)
                except forms.ValidationError as error:
                    self.add_error('password', error)
        return cleaned_data

    def save(self):
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        return User.objects.create_user(
            username=username,
            email=email,
            password=password
        )


class LoginForm(forms.Form):
    login = forms.CharField(
        label='E-posta veya Kullanıcı Adı',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'ornek@eposta.com veya kullanici_adi',
            'class': 'form-input',
            'autocomplete': 'username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Parola',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Parolanız',
            'class': 'form-input',
            'autocomplete': 'current-password',
        })
    )

    def __init__(self, *args, **kwargs):
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        login_val = cleaned_data.get('login', '').strip()
        password = cleaned_data.get('password')

        if login_val and password:
            user = User.objects.filter(
                Q(username__iexact=login_val) | Q(email__iexact=login_val)
            ).first()

            if user is None:
                raise forms.ValidationError('Kullanıcı adı / e-posta veya parola hatalı.')

            authenticated_user = authenticate(username=user.username, password=password)
            if authenticated_user is None:
                raise forms.ValidationError('Kullanıcı adı / e-posta veya parola hatalı.')

            if not authenticated_user.is_active:
                raise forms.ValidationError('Bu hesap devre dışı bırakılmış.')

            self.user_cache = authenticated_user
        return cleaned_data

    def get_user(self):
        return self.user_cache
