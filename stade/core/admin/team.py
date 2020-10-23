from django.contrib import admin
from girder_utils.admin import ReadonlyTabularInline

from stade.core.models import Team

from .approach import ApproachInline


class TeamInline(ReadonlyTabularInline):
    model = Team
    fields = ['id', 'name', 'num_users']

    def num_users(self, obj):
        return obj.users.count()


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['challenge', 'name']
    list_display_links = ['name']
    list_filter = ['challenge__name']

    autocomplete_fields = ['creator', 'users']

    inlines = [ApproachInline]
