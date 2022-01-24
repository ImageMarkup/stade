from datetime import datetime, timedelta
from typing import cast

from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from girder_utils.db import SelectRelatedManager
from s3_file_field import S3FileField

from .challenge import Challenge
from .submission import Submission
from .team import Team


class Task(models.Model):
    class Meta:
        ordering = ['id']

    class Type(models.TextChoices):
        SEGMENTATION = 'segmentation', _('Segmentation')
        CLASSIFICATION = 'classification', _('Classification')

    class MetricField(models.TextChoices):
        BALANCED_ACCURACY = 'balanced_accuracy', _('Balanced Accuracy')
        AVERAGE_PRECISION = 'ap', _('Average Precision')
        AUC = 'auc', _('AUC')

    type = models.CharField(max_length=20, choices=Type.choices)
    metric_field = models.CharField(
        max_length=100,
        choices=MetricField.choices,
        help_text='Which metric to use for the overall score',
    )
    created = models.DateTimeField(default=timezone.now)
    challenge = models.ForeignKey(Challenge, on_delete=models.DO_NOTHING, related_name='tasks')
    name = models.CharField(max_length=100)
    description = models.TextField()
    short_description = models.TextField()
    locked = models.BooleanField(
        default=True,
        help_text='Whether users are blocked from making and editing approaches and submissions.',
    )
    hidden = models.BooleanField(
        default=True, help_text='Whether the GUI exposes this task to users.'
    )
    scores_published = models.BooleanField(
        default=False,
        help_text='Whether final scores are visible to submitters and the leaderboard is open.',
    )
    max_approaches = models.PositiveSmallIntegerField(
        verbose_name='Maximum approaches',
        default=3,
        help_text=(
            'The maximum number of approaches a team can make on this task. Set to 0 to disable.'
        ),
    )
    max_submissions_per_week = models.PositiveSmallIntegerField(
        verbose_name='Maximum submissions per week',
        default=10,
        help_text=(
            'The maximum number of submissions a team can make to this task per week. '
            'Set to 0 to disable.'
        ),
    )
    requires_manuscript = models.BooleanField(
        verbose_name='Requires a manuscript',
        default=True,
        help_text='Whether approaches should require a manuscript.',
    )
    test_ground_truth_file = S3FileField()

    # Define custom "objects" first, so it will be the "_default_manager", which is more efficient
    # for many automatically generated queries
    objects = SelectRelatedManager('challenge')

    def __str__(self):
        return f'{self.challenge.name}: {self.name}'

    @property
    def allowed_submission_extension(self):
        return {self.Type.SEGMENTATION: 'zip', self.Type.CLASSIFICATION: 'csv'}[self.type]

    def get_absolute_url(self):
        return reverse('task-detail', args=[self.id])

    def pending_or_succeeded_submissions(self, team_or_user) -> QuerySet[Submission]:
        filters = {
            'status__in': [
                Submission.Status.QUEUED,
                Submission.Status.SCORING,
                Submission.Status.SUCCEEDED,
            ],
            'approach__task': self,
        }

        if isinstance(team_or_user, Team):
            filters['approach__team'] = team_or_user
        elif isinstance(team_or_user, User):
            filters['creator'] = team_or_user

        return Submission.objects.filter(**filters)

    def next_available_submission(self, team) -> datetime | None:
        """
        Return a datetime of when the next submission can be made.

        Returns None if the submission can be made now.
        """
        if self.max_submissions_per_week == 0:
            return None

        one_week_ago = timezone.now() - timedelta(weeks=1)

        submissions_in_last_week = (
            self.pending_or_succeeded_submissions(team)
            .filter(created__gte=one_week_ago)
            .order_by('created')
        )

        if len(submissions_in_last_week) >= self.max_submissions_per_week:
            oldest_submission_in_last_week = cast(Submission, submissions_in_last_week.first())
            return oldest_submission_in_last_week.created + timedelta(weeks=1)
        else:
            return None
