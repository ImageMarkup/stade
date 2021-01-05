from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify


class Challenge(models.Model):
    class Meta:
        ordering = ['position']

    created = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    locked = models.BooleanField(
        default=True, help_text='Whether users are blocked from making and editing teams.'
    )
    position = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name

    @cached_property
    def stats(self):
        from stade.core.models import Approach, Submission, Task

        d = {}
        d['num_successful_approaches'] = Approach.successful.filter(
            task__challenge=self,
        ).count()
        d['num_total_submissions'] = Submission.objects.filter(
            approach__task__challenge=self,
        ).count()

        d['tasks'] = (
            Task.objects.annotate(
                num_total_submissions=models.Count(
                    'approach__submission',
                    distinct=True,
                ),
                num_successful_approaches=models.Count('approach', distinct=True),
            )
            .filter(challenge=self)
            .values()
        )
        return d

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
