from django.db import models

from tracker.tasks import add_mailchimp_subscriber


class Email(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        add_mailchimp_subscriber.delay(self.email)
