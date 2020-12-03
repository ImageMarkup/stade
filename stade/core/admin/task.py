from django.contrib import admin
from girder_utils.admin import ReadonlyTabularInline

from stade.core.models import Task


class TaskInline(ReadonlyTabularInline):
    model = Task
    fields = ['id', 'name', 'type', 'locked', 'hidden', 'scores_published']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['challenge', 'name', 'locked']
    list_display_links = ['name']
    list_filter = ['locked', 'type', 'metric_field']
    search_fields = ['name']
