from django.contrib import admin

from core.models import Approach, Team, TeamInvitation
from core.tasks import score_submission
from .models import Challenge, Submission, Task


def rescore_submission_without_notifying(modeladmin, request, queryset):
    for submission in queryset:
        score_submission.delay(submission.id, notify=False)


rescore_submission_without_notifying.short_description = (  # type: ignore
    'Rescore (without notifying)'
)


def rescore_submission_with_notification(modeladmin, request, queryset):
    for submission in queryset:
        score_submission.delay(submission.id, notify=True)


rescore_submission_with_notification.short_description = (  # type: ignore
    'Rescore (with notification)'
)


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

    actions = [rescore_submission_with_notification, rescore_submission_without_notifying]


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
