from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from core.models import Approach, TeamInvitation, Team


class AcceptInvitationForm(forms.Form):
    invitation_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    # make sure the form hasn't been forged
    def clean_invitation_id(self):
        invitation_id = self.cleaned_data["invitation_id"]
        invite = get_object_or_404(TeamInvitation, pk=invitation_id)
        if invite.recipient != self.request.user:
            raise forms.ValidationError("invalid invitation id")
        return invitation_id


class CreateTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "institution"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)


class CreateApproachForm(forms.ModelForm):
    class Meta:
        model = Approach
        fields = ["name", "uses_external_data", "manuscript"]

    def __init__(self, *args, **kwargs):
        self.team = get_object_or_404(Team, pk=kwargs['team_id'])
        self.request = kwargs.pop("request", None)
        kwargs.pop('team_id', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        if Approach.objects.filter(team=self.team).count() >= settings.MAX_APPROACHES:
            raise ValidationError(
                f"Only {settings.MAX_APPROACHES} approaches are allowed per team."
            )
