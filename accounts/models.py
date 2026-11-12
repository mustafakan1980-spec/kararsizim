from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    username_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9_]{3,20}$',
        message='Kullanıcı adı 3-20 karakter arasında olmalı ve yalnızca harf, rakam ve alt çizgi (_) içermelidir.'
    )

    username = models.CharField(
        max_length=20,
        unique=True,
        validators=[username_validator],
        help_text='3-20 karakter, yalnızca harf, rakam ve alt çizgi (_).'
    )
    email = models.EmailField(
        unique=True,
        blank=False,
        null=False
    )

    def clean(self):
        super().clean()
        if self.username:
            self.username = self.username.lower()
        if self.email:
            self.email = self.email.lower()

    def save(self, *args, **kwargs):
        if self.username:
            self.username = self.username.lower()
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
