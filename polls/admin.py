from django.contrib import admin
from .models import Option, Poll, Vote


class OptionInline(admin.TabularInline):
    model = Option
    extra = 0
    min_num = 2
    max_num = 5
    fields = ('position', 'text')
    ordering = ['position']


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question', 'author', 'created_at', 'is_active', 'option_count', 'vote_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question', 'author__username')
    inlines = [OptionInline]
    readonly_fields = ('created_at',)

    def option_count(self, obj):
        return obj.options.count()
    option_count.short_description = 'Seçenek'

    def vote_count(self, obj):
        return obj.votes.count()
    vote_count.short_description = 'Oy'


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('poll', 'option', 'user', 'anon_token', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('poll__question', 'user__username')
    readonly_fields = ('created_at',)
