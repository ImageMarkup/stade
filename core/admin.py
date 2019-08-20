from django.contrib import admin

from core.models import Approach, Team, TeamInvitation
from .models import Challenge, Submission, Task


class ApproachInline(admin.TabularInline):
    model = Approach
    show_change_link = True
    extra = 0


class SubmissionInline(admin.TabularInline):
    pass


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['approach', 'id', 'status']
    list_display_links = ['id']
    list_filter = ['status']

    autocomplete_fields = ['creator', 'approach']

    # exclude detailed metrics from the form since they're big and impractical to edit
    exclude = ['score']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    pass


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['challenge', 'name']
    list_display_links = ['name']
    list_filter = ['challenge__name']

    autocomplete_fields = ['creator', 'users']

    inlines = [ApproachInline]


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = ['created', 'team_name', 'sender', 'recipient']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # TODO: Filter for permissions if non-superusers gain access to admin panel
        qs = qs.select_related('team', 'sender')
        return qs

    def team_name(self, invitation):
        return invitation.team.name


@admin.register(Approach)
class ApproachAdmin(admin.ModelAdmin):
    list_display = ['task', 'team', 'name']
    list_display_links = ['name']
    list_filter = ['task']

    search_fields = ['name']
