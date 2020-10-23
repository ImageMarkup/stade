from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from .team import Team


class TeamInvitation(models.Model):
    created = models.DateTimeField(default=timezone.now)
    sender = models.ForeignKey(
        get_user_model(), related_name='sent_invites', on_delete=models.CASCADE
    )
    recipient = models.EmailField(db_index=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.team} invite'
