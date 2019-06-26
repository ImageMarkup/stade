from django.contrib import admin

from tracker.models import Email

from import_export.admin import ExportActionMixin


@admin.register(Email)
class EmailAdmin(ExportActionMixin, admin.ModelAdmin):
    model = Email
    list_display = ("email", "created")


from import_export import resources


class EmailResource(resources.ModelResource):
    class Meta:
        model = Email
