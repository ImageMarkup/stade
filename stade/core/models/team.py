from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone

from .challenge import Challenge


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
