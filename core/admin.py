from django.contrib import admin

from .models import Submission, Task, Challenge
from core.models import Approach, Team, TeamInvitation
from core.tasks import rescore_task_submissions


def rescore_task(modeladmin, request, queryset):
    for task in queryset:
        rescore_task_submissions.delay(task.id)


rescore_task.short_description = "Rescore task submissions"


class SubmissionInline(admin.TabularInline):
    model = Submission


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    actions = [rescore_task]


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    model = Challenge


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    model = Team


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    model = TeamInvitation


@admin.register(Approach)
class ApproachAdmin(admin.ModelAdmin):
    model = Approach
