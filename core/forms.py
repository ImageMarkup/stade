from allauth.account.forms import SignupForm
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from core.models import Approach, Submission, Team, TeamInvitation


class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'] = forms.CharField()
        self.fields['last_name'] = forms.CharField()

    def save(self, request):
        user = super().save(request)
        user.email = user.email.lower()
        user.save()
        return user


class AcceptInvitationForm(forms.Form):
    invitation_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    # make sure the form hasn't been forged
    def clean_invitation_id(self):
        invitation_id = self.cleaned_data['invitation_id']
        invite = get_object_or_404(TeamInvitation, pk=invitation_id)
        if invite.recipient != self.request.user:
            raise forms.ValidationError('invalid invitation id')
        return invitation_id


class CreateInvitationForm(forms.ModelForm):
    class Meta:
        model = TeamInvitation
        fields = ['recipient']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.team_id = kwargs.pop('team_id', None)
        super().__init__(*args, **kwargs)

    def clean_recipient(self):
        return self.cleaned_data['recipient'].lower()

    def clean(self):
        team = get_object_or_404(self.request.user.teams, pk=self.team_id)
        if team.users.filter(email=self.cleaned_data['recipient']).exists():
            raise forms.ValidationError('User is already in the team')


class CreateTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'institution', 'institution_url']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)


class CreateSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['accepted_terms', 'test_prediction_file']

        error_messages = {
            'test_prediction_file': {'required': _('You must provide a prediction file.')}
        }

    def clean_accepted_terms(self):
        data = self.cleaned_data['accepted_terms']
        if not data:
            raise forms.ValidationError('You must accept the data sharing policy terms.')

        return data


class CreateApproachForm(forms.ModelForm):
    class Meta:
        model = Approach
        fields = ['name', 'uses_external_data', 'manuscript']

    def __init__(self, *args, **kwargs):
        self.team = get_object_or_404(Team, pk=kwargs['team_id'])
        self.request = kwargs.pop('request', None)
        kwargs.pop('team_id', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        if Approach.objects.filter(team=self.team).count() >= settings.MAX_APPROACHES:
            raise ValidationError(
                f'Only {settings.MAX_APPROACHES} approaches are allowed per team.'
            )
