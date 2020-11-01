from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .approach import Approach


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
