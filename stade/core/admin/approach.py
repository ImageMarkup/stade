from django.contrib import admin
from girder_utils.admin import ReadonlyTabularInline

from stade.core.models import Approach

from .submission import SubmissionInline


class ApproachInline(ReadonlyTabularInline):
    model = Approach
    fields = ['id', 'task', 'created', 'name', 'manuscript']


@admin.register(Approach)
class ApproachAdmin(admin.ModelAdmin):
    list_display = ['task', 'team', 'name']
    list_display_links = ['name']
    list_filter = ['task']

    search_fields = ['name']

    inlines = [SubmissionInline]
