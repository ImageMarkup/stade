from typing import List, Optional, Tuple

from django.contrib import admin
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_admin_display import admin_display
from girder_utils.admin import ReadonlyTabularInline

from stade.core.models import Submission, Task
from stade.core.tasks import score_submission


class SubmissionInline(ReadonlyTabularInline):
    model = Submission
    fields = ['id', 'created', 'test_prediction_file', 'status', 'overall_score', 'team_name']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('approach__team')
        return qs

    def team_name(self, obj):
        return obj.approach.team.name


class TaskListFilter(admin.SimpleListFilter):
    title = _('task')
    parameter_name = 'approach__task'

    # Remove type ignore on release of https://github.com/typeddjango/django-stubs/pull/217
    def lookups(self, request, model_admin) -> List[Tuple[int, str]]:  # type: ignore
        # Sorting has to be done in python because the string representation of a task
        # differs from the name.
        return sorted(
            [(t.id, str(t)) for t in Task.objects.all()], key=lambda x: str(x[1]), reverse=True
        )

    def queryset(self, request, queryset) -> 'Optional[QuerySet[Task]]':
        if self.value():
            return queryset.filter(approach__task=self.value())
        else:
            return None


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = [
        'created',
        'id',
        'task',
        '_creator',
        '_creator_fingerprint_id',
        '_creator_ip',
        'status',
    ]
    list_display_links = ['id']
    list_filter = ['status', TaskListFilter]

    search_fields = ['creator__email', 'creator_ip', 'creator_fingerprint']
    autocomplete_fields = ['creator', 'approach']

    # exclude detailed metrics from the form since they're big and impractical to edit
    exclude = ['score']

    actions = ['rescore_submission_with_notification', 'rescore_submission_without_notifying']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('creator', 'approach', 'approach__task', 'approach__task__challenge')
        return qs

    @mark_safe
    def _creator(self, obj):
        if not obj.creator.is_active:
            user = f'<strike>{obj.creator.email}</strike>'
        else:
            user = obj.creator.email

        return f'<a href="%s">View</a>: {user} ' % (
            reverse('admin:auth_user_change', args=(obj.creator.id,)),
        )

    _creator.short_description = 'Creator'
    _creator.allow_tags = True

    def _creator_fingerprint_id(self, obj):
        return obj.creator_fingerprint_id

    _creator_fingerprint_id.short_description = 'Fingerprint'

    def _creator_ip(self, obj):
        return obj.creator_ip

    _creator_ip.short_description = 'IP'

    @admin_display(admin_order_field='approach__task')
    def task(self, obj: Submission):
        return obj.approach.task

    @admin_display(short_description='Rescore (without notifying)')
    def rescore_submission_without_notifying(self, request, queryset):
        for submission in queryset:
            score_submission.delay(submission.id, notify=False)

    @admin_display(short_description='Rescore (with notification)')
    def rescore_submission_with_notification(self, request, queryset):
        for submission in queryset:
            score_submission.delay(submission.id, notify=True)
