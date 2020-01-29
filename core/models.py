from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import PurePath
from typing import cast, Optional
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.postgres.fields.jsonb import JSONField
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.db.models import Exists, OuterRef, QuerySet
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# Don't use this, it will be deleted when past migrations are squashed.
# See CollisionSafeFileField instead.
def _deprecated_file_upload_to(instance, filename):
    extension = PurePath(filename).suffix[1:].lower()
    return f'{uuid4()}.{extension}'


task_data_file_upload_to = _deprecated_file_upload_to
submission_file_upload_to = _deprecated_file_upload_to


class CollisionSafeFileField(models.FileField):
    description = 'A file field which is uploaded to <randomuuid>/filename.'

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 200)
        kwargs['upload_to'] = self.uuid_prefix_filename
        super().__init__(*args, **kwargs)

    @staticmethod
    def uuid_prefix_filename(instance, filename):
        return f'{uuid4()}/{filename}'


class DeferredFieldsManager(models.Manager):
    def __init__(self, *deferred_fields):
        self.deferred_fields = deferred_fields
        super().__init__()

    def get_queryset(self):
        return super().get_queryset().defer(*self.deferred_fields)


class SelectRelatedManager(models.Manager):
    def __init__(self, *related_fields):
        self.related_fields = related_fields
        super().__init__()

    def get_queryset(self):
        return super().get_queryset().select_related(*self.related_fields)


class SuccessfulApproachesManager(models.Manager):
    def get_queryset(self):
        successful_submissions = Submission.objects.filter(
            approach=OuterRef('pk'), status=Submission.Status.SUCCEEDED
        )
        return super().get_queryset().filter(Exists(successful_submissions))


class Challenge(models.Model):
    class Meta:
        ordering = ['position']

    created = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=100, unique=True)
    locked = models.BooleanField(
        default=True, help_text='Whether users are blocked from making and editing teams.'
    )
    position = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class Task(models.Model):
    class Meta:
        ordering = ['id']

    class Type(models.TextChoices):
        SEGMENTATION = 'segmentation', _('Segmentation')
        CLASSIFICATION = 'classification', _('Classification')

    type = models.CharField(max_length=20, choices=Type.choices)
    created = models.DateTimeField(default=timezone.now)
    challenge = models.ForeignKey(Challenge, on_delete=models.DO_NOTHING, related_name='tasks')
    name = models.CharField(max_length=100)
    description = models.TextField()
    short_description = models.TextField()
    locked = models.BooleanField(
        default=True,
        help_text='Whether users are blocked from making and editing approaches and submissions.',
    )
    hidden = models.BooleanField(default=True, help_text='Whether the task is invisible to users.')
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
    test_ground_truth_file = CollisionSafeFileField()

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

    def pending_or_succeeded_submissions(self, team) -> QuerySet[Submission]:
        return Submission.objects.filter(
            status__in=[
                Submission.Status.QUEUED,
                Submission.Status.SCORING,
                Submission.Status.SUCCEEDED,
            ],
            approach__task=self,
            approach__team=team,
        )

    def next_available_submission(self, team) -> Optional[datetime]:
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


class Team(models.Model):
    class Meta:
        unique_together = ('challenge', 'name')

    created = models.DateTimeField(default=timezone.now)
    creator = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100)
    institution = models.CharField(max_length=100, blank=True)
    institution_url = models.URLField(blank=True)
    users = models.ManyToManyField(get_user_model(), related_name='teams')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name}'

    def user_full_names(self):
        return sorted([x.get_full_name() for x in self.users.all()])

    # todo, this doesn't work at all
    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.pk is None:
            # do in a transaction
            super().save(*args, **kwargs)
            self.users.add(self.creator)
        else:
            super().save(*args, **kwargs)


class TeamInvitation(models.Model):
    created = models.DateTimeField(default=timezone.now)
    sender = models.ForeignKey(
        get_user_model(), related_name='sent_invites', on_delete=models.CASCADE
    )
    recipient = models.EmailField(db_index=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.team} invite'


class Submission(models.Model):
    class Meta:
        ordering = ['-created']

    class Status(models.TextChoices):
        QUEUED = 'queued', _('Queued for scoring')
        SCORING = 'scoring', _('Scoring')
        INTERNAL_FAILURE = 'internal_failure', _('Internal failure')
        FAILED = 'failed', _('Failed')
        SUCCEEDED = 'succeeded', _('Succeeded')

    created = models.DateTimeField(default=timezone.now)
    creator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    approach = models.ForeignKey('Approach', on_delete=models.CASCADE)
    accepted_terms = models.BooleanField(default=False)
    test_prediction_file = CollisionSafeFileField()
    status = models.CharField(max_length=20, default=Status.QUEUED, choices=Status.choices)
    score = JSONField(blank=True, null=True)
    overall_score = models.FloatField(blank=True, null=True)
    validation_score = models.FloatField(blank=True, null=True)
    fail_reason = models.TextField(blank=True)

    objects = DeferredFieldsManager('score')

    def __str__(self):
        return f'{self.id}'

    def get_absolute_url(self):
        return reverse('submission-detail', args=[self.id])

    def reset_scores(self):
        self.score = None
        self.overall_score = None
        self.validation_score = None
        return self


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
    manuscript = CollisionSafeFileField(
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
    def latest_successful_submission(self) -> Optional[Submission]:
        return (
            Submission.objects.filter(approach=self, status=Submission.Status.SUCCEEDED)
            .order_by('-created')
            .first()
        )


class SubmissionApproach(models.Model):
    class Meta:
        managed = False
        db_table = 'view_submission_approach'

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    approach = models.ForeignKey(Approach, on_delete=models.DO_NOTHING)
    team = models.ForeignKey(Team, on_delete=models.DO_NOTHING)
    submission = models.OneToOneField(Submission, on_delete=models.DO_NOTHING, primary_key=True)
    review_state = models.CharField(max_length=27)
    overall_score = models.FloatField()

    @staticmethod
    def index_by_approach(qs: QuerySet[SubmissionApproach]):
        ret = {}
        for sa in qs:
            ret[sa.approach.id] = sa
        return ret


class ReviewHistory(models.Model):
    class Meta:
        ordering = ['-created']

    approach = models.ForeignKey(Approach, on_delete=models.CASCADE, related_name='review_history')
    reviewed_by = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    created = models.DateTimeField(default=timezone.now)
    review_state = models.CharField(max_length=8, choices=Approach.ReviewState.choices)
    reject_reason = models.CharField(
        max_length=27, blank=True, default='', choices=Approach.RejectReason.choices
    )


@receiver(pre_save, sender=Approach)
def reset_review_state_on_manuscript_change(sender, instance: Approach, **kwargs):
    if instance.id:
        old_approach = Approach.objects.get(pk=instance.id)

        if old_approach.manuscript != instance.manuscript:
            instance.review_state = ''


@receiver(pre_save, sender=User)
def set_username_to_email_address(sender, instance: User, **kwargs):
    """Forcibly sets the username of every user to their email address."""
    instance.username = instance.email
