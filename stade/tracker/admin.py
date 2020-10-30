from django.contrib import admin
from import_export import resources
from import_export.admin import ExportActionMixin

from stade.tracker.models import Email


@admin.register(Email)
class EmailAdmin(ExportActionMixin, admin.ModelAdmin):
    model = Email
    list_display = ['email', 'created']


class EmailResource(resources.ModelResource):
    class Meta:
        model = Email
