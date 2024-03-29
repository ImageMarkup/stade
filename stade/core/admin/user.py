from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils.safestring import mark_safe

from .submission import SubmissionInline


class UserAdmin(BaseUserAdmin):
    ordering = ['-date_joined']
    inlines = [SubmissionInline]
    list_display = [
        'date_joined',
        'formatted_email',
        'name',
        'num_teams',
        'num_approaches',
        'num_submissions',
        'is_staff',
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            num_teams=Count('team', distinct=True),
            num_approaches=Count('team__approach', distinct=True),
            num_submissions=Count('team__approach__submission', distinct=True),
        )
        return qs

    @admin.display(description='Num Teams', ordering='num_teams')
    def num_teams(self, obj):
        return obj.num_teams

    @admin.display(description='Num Approaches', ordering='num_approaches')
    def num_approaches(self, obj):
        return obj.num_approaches

    @admin.display(description='Num Submissions', ordering='num_submissions')
    def num_submissions(self, obj):
        return obj.num_submissions

    def name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    @mark_safe
    @admin.display(description='Email')
    def formatted_email(self, obj):
        if not obj.is_active:
            user = f'<strike>{obj.email}</strike>'
        else:
            user = obj.email

        return user


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
