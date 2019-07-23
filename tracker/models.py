from django.db import IntegrityError, models
from django.utils import timezone

from tracker.tasks import add_mailchimp_subscriber


class Email(models.Model):
    created = models.DateTimeField(default=timezone.now)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            add_mailchimp_subscriber.delay(self.email)
        except IntegrityError:
            # Email already exists
            pass
