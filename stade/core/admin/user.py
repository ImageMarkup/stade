from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

from .team import TeamInline


class UserAdmin(BaseUserAdmin):
    ordering = ['-date_joined']
    inlines = [TeamInline]
    list_display = ['date_joined', '_email', 'name', 'is_staff']

    def name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    @mark_safe
    def _email(self, obj):
        if not obj.is_active:
            user = f'<strike>{obj.email}</strike>'
        else:
            user = obj.email

        return user

    _email.short_description = 'Email'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
