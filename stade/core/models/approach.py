from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Exists, OuterRef
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from s3_file_field import S3FileField

from .submission import Submission
from .task import Task
from .team import Team


class SuccessfulApproachesManager(models.Manager):
    def get_queryset(self):
        successful_submissions = Submission.objects.filter(
            approach=OuterRef('pk'), status=Submission.Status.SUCCEEDED
        )
        return super().get_queryset().filter(Exists(successful_submissions))


class Approach(models.Model):
    class Meta:
        verbose_name_plural = 'approaches'
        constraints = [
            models.UniqueConstraint(fields=['name', 'task', 'team'], name='unique_approaches')
        ]

    class ReviewState(models.TextChoices):
        ACCEPTED = 'accepted', _('Accepted')
        REJECTED = 'rejected', _('Rejected')

    class RejectReason(models.TextChoices):
        BLANK_OR_CORRUPT_MANUSCRIPT = (
            'blank_or_corrupt_manuscript',
            _('Blank or corrupt manuscript'),
        )
        LOW_QUALITY_MANUSCRIPT = 'low_quality_manuscript', _('Low quality manuscript')
        RULE_VIOLATION = 'rule_violation', _('Violation of rules')

    created = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    docker_tag = models.CharField(blank=True, max_length=120)
    uses_external_data = models.BooleanField(default=False, choices=((True, 'Yes'), (False, 'No')))
    manuscript = S3FileField(
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])], blank=True
    )

    review_assignee = models.ForeignKey(
        get_user_model(), null=True, blank=True, on_delete=models.DO_NOTHING
    )
    review_state = models.CharField(
        max_length=8, blank=True, default='', choices=ReviewState.choices
    )
    reject_reason = models.CharField(
        max_length=27, blank=True, default='', choices=RejectReason.choices
    )

    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    objects = models.Manager()
    successful = SuccessfulApproachesManager()

    def __str__(self):
        return self.name

    @property
    def latest_submission(self):
        return Submission.objects.filter(approach=self).order_by('-created').first()

    @property
    def latest_successful_submission(self) -> Submission | None:
        return (
            Submission.objects.filter(approach=self, status=Submission.Status.SUCCEEDED)
            .order_by('-created')
            .first()
        )
