from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from s3_file_field import S3FileField


class DeferredFieldsManager(models.Manager):
    def __init__(self, *deferred_fields):
        self.deferred_fields = deferred_fields
        super().__init__()

    def get_queryset(self):
        return super().get_queryset().defer(*self.deferred_fields)


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
    creator_fingerprint_id = models.CharField(max_length=32, null=True, blank=True)
    creator_ip = models.GenericIPAddressField(null=True, blank=True)
    approach = models.ForeignKey('Approach', on_delete=models.CASCADE)
    accepted_terms = models.BooleanField(default=False)
    test_prediction_file = S3FileField()
    status = models.CharField(max_length=20, default=Status.QUEUED, choices=Status.choices)
    score = models.JSONField(blank=True, null=True)
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
