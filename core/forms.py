from allauth.account.forms import SignupForm
from django import forms
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from core.models import Approach, Submission, Team, TeamInvitation, Task


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
        super().clean()
        team = get_object_or_404(self.request.user.teams, pk=self.team_id)
        if team.users.filter(email=self.cleaned_data['recipient']).exists():
            raise forms.ValidationError(f'{self.cleaned_data["recipient"]} is already in the team')
        if TeamInvitation.objects.filter(
            recipient=self.cleaned_data['recipient'], team_id=team.id
        ).exists():
            raise forms.ValidationError(
                f'{self.cleaned_data["recipient"]} has already been invited'
            )


class CreateTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'institution', 'institution_url']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.task_id = kwargs.pop('task_id', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        task = get_object_or_404(Task.objects, pk=self.task_id)

        if task.challenge.locked:
            raise ValidationError(f'The {task.challenge.name} challenge is locked.')


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
        self.team_id = kwargs.pop('team_id', None)
        self.task_id = kwargs.pop('task_id', None)
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        team = get_object_or_404(self.request.user.teams, pk=self.team_id)
        task = get_object_or_404(Task, pk=self.task_id)

        if task.locked:
            raise ValidationError(f'The task {task.name} is locked.')

        if Approach.objects.filter(team=team, task=task).count() >= task.max_approaches:
            raise ValidationError(
                f'You\'ve reached the maximum number of approaches for {task.name}.'
            )
