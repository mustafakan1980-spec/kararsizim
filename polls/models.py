from django.conf import settings
from django.db import models
from django.db.models import Q


class Poll(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='polls'
    )
    question = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.question


class Option(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name='options'
    )
    text = models.CharField(max_length=80)
    position = models.PositiveSmallIntegerField()  # 0-4

    class Meta:
        ordering = ['position']
        constraints = [
            models.UniqueConstraint(
                fields=['poll', 'position'],
                name='unique_poll_option_position'
            )
        ]

    def __str__(self):
        return f"{self.poll_id} — {self.text}"


class Vote(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='votes'
    )
    anon_token = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # user veya anon_token'dan tam olarak biri dolu olmalı
            models.CheckConstraint(
                condition=(
                    Q(user__isnull=False, anon_token__isnull=True) |
                    Q(user__isnull=True, anon_token__isnull=False)
                ),
                name='vote_user_or_anon_token'
            ),
            # Kayıtlı kullanıcı her ankete tek oy
            models.UniqueConstraint(
                fields=['poll', 'user'],
                condition=Q(user__isnull=False),
                name='unique_vote_per_user'
            ),
            # Anonim kullanıcı her ankete tek oy
            models.UniqueConstraint(
                fields=['poll', 'anon_token'],
                condition=Q(anon_token__isnull=False),
                name='unique_vote_per_anon'
            ),
        ]

    def __str__(self):
        who = self.user.username if self.user else f"anon:{self.anon_token[:8]}"
        return f"{who} → {self.poll_id}"
