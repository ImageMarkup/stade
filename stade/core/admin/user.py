from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django_admin_display import admin_display

from .team import TeamInline


class UserAdmin(BaseUserAdmin):
    ordering = ['-date_joined']
    inlines = [TeamInline]
    list_display = ['date_joined', 'formatted_email', 'name', 'is_staff']

    def name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    @mark_safe
    @admin_display(short_description='Email')
    def formatted_email(self, obj):
        if not obj.is_active:
            user = f'<strike>{obj.email}</strike>'
        else:
            user = obj.email

        return user


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
