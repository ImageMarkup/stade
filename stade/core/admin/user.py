from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .team import TeamInline


class UserAdmin(BaseUserAdmin):
    inlines = [TeamInline]
    list_display = ['date_joined'] + list(BaseUserAdmin.list_display)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
