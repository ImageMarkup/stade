from django.db import models
from django.utils import timezone
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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
