from django.contrib import admin

from stade.core.models import Challenge

from .task import TaskInline


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    inlines = [TaskInline]
