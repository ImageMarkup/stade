from pathlib import PurePath
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields.jsonb import JSONField
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone


def task_data_file_upload_to(instance, filename):
    extension = PurePath(filename).suffix[1:].lower()
    return f'{uuid4()}.{extension}'


def submission_file_upload_to(instance, filename):
    extension = PurePath(filename).suffix[1:].lower()
    return f'{uuid4()}.{extension}'


class Challenge(models.Model):
    created = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=100, unique=True)
    locked = models.BooleanField(
        default=True, help_text='Whether users are blocked from making and editing teams.'
    )
    position = models.PositiveSmallIntegerField(default=0)

    ordering = ['-position']

    def __str__(self):
        return self.name


TASK_TYPE_CHOICES = {'segmentation': 'Segmentation', 'classification': 'Classification'}


class Task(models.Model):
    type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES.items())
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
        verbose_name='Maxium Approaches',
        default=3,
        help_text='The maximum number of approaches a team can make on this task.',
    )
    test_ground_truth_file = models.FileField(upload_to=task_data_file_upload_to)

    def __str__(self):
        return f'{self.challenge.name}: {self.name}'

    def get_absolute_url(self):
        return reverse('task-detail', args=[self.id])


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
    recipient = models.EmailField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.team} invite'


SUBMISSION_STATUS_CHOICES = {
    'queued': 'Queued for scoring',
    'scoring': 'Scoring',
    'internal_failure': 'Internal failure',
    'failed': 'Failed',
    'succeeded': 'Succeeded',
}


class Submission(models.Model):
    created = models.DateTimeField(default=timezone.now)
    creator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    approach = models.ForeignKey('Approach', on_delete=models.CASCADE)
    accepted_terms = models.BooleanField(default=False)
    test_prediction_file = models.FileField(upload_to=submission_file_upload_to)
    test_prediction_file_name = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20, default='queued', choices=SUBMISSION_STATUS_CHOICES.items()
    )
    score = JSONField(blank=True, null=True)
    overall_score = models.FloatField(blank=True, null=True)
    fail_reason = models.TextField(blank=True)

    ordering = ['-created']

    def __str__(self):
        return f'{self.id}'

    def get_absolute_url(self):
        return reverse('submission-detail', args=[self.id])


class ScoreHistory(models.Model):
    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name='score_history'
    )
    created = models.DateTimeField(default=timezone.now)
    score = JSONField()
    overall_score = models.FloatField()

    ordering = ['-created']


class Approach(models.Model):
    class Meta:
        verbose_name_plural = 'approaches'

    created = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=100)
    uses_external_data = models.BooleanField()
    manuscript = models.FileField(
        upload_to=submission_file_upload_to,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        max_length=200,
        blank=True,
    )
    manuscript_name = models.CharField(max_length=200, blank=True, null=True)

    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    @property
    def latest_submission(self):
        return Submission.objects.filter(approach=self).order_by('-created').first()

    @property
    def friendly_status(self):
        return SUBMISSION_STATUS_CHOICES[self.latest_submission.status]

    @property
    def score(self):
        return self.latest_submission.overall_score
