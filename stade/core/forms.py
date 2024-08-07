import logging
from pathlib import PurePath

from allauth.account.forms import ResetPasswordKeyForm, SignupForm
from allauth.account.models import EmailAddress
from django import forms
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
import requests

from stade.core.models import Approach, Challenge, Submission, Task, Team, TeamInvitation
from stade.tracker.tasks import add_mailchimp_subscriber

logger = logging.getLogger(__name__)


class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'] = forms.CharField()
        self.fields['last_name'] = forms.CharField()
        self.fields['subscribe'] = forms.BooleanField(required=False)

    def clean_email(self):
        super().clean_email()
        domain = self.cleaned_data['email'].split('@')[-1]

        try:
            r = requests.get(f'https://open.kickbox.com/v1/disposable/{domain}', timeout=(2, 2))
        except ConnectionError:
            # Ignore the intermittent failure and let them register (this should be rare)
            return self.cleaned_data['email']

        if r.ok and r.json()['disposable']:
            raise ValidationError('This looks like a fake email address.')
        elif not r.ok:
            logger.warning(f'Failed to check email address authenticity ({r.status_code}).')

        return self.cleaned_data['email']

    def save(self, request):
        user = super().save(request)
        user.email = user.email.lower()
        user.save()

        if self.cleaned_data['subscribe']:
            add_mailchimp_subscriber.delay(user.email)

        return user


class CustomResetPasswordKeyForm(ResetPasswordKeyForm):
    """
    Provide a custom form for setting password.

    This causes resetting a password to imply the email has been verified.
    """

    def save(self):
        email = EmailAddress.objects.filter(email=self.user.email).first()

        # Note this logic is inlined from allauth.account.views.confirm_email. We don't have
        # access to a request object here so we cannot call it directly.
        email.verified = True
        email.set_as_primary(conditional=True)
        email.save()
        super().save()


class AcceptInvitationForm(forms.Form):
    invitation_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    # make sure the form hasn't been forged
    def clean_invitation_id(self):
        invitation_id = self.cleaned_data['invitation_id']
        invite = get_object_or_404(TeamInvitation, pk=invitation_id)
        if invite.recipient != self.request.user.email:
            # This should never fail.
            # These errors never get displayed to users, so log to sentry
            logger.error(f'Invalid invitation id {invitation_id}')
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
        team = get_object_or_404(self.request.user.teams, pk=self.team_id)
        recipient = self.cleaned_data['recipient'].lower()

        if team.users.filter(email=recipient).exists():
            raise forms.ValidationError(f'{recipient} is already in the team.')

        if TeamInvitation.objects.filter(recipient=recipient, team_id=team.id).exists():
            raise forms.ValidationError(f'{recipient} has already been invited.')

        return self.cleaned_data['recipient'].lower()


class TeamForm(forms.ModelForm):
    initial_invite_1 = forms.EmailField(required=False)
    initial_invite_2 = forms.EmailField(required=False)
    initial_invite_3 = forms.EmailField(required=False)

    class Meta:
        model = Team
        fields = ['name', 'institution', 'institution_url']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.instance = kwargs.get('instance', None)
        self.task_id = kwargs.pop('task_id', None)
        self.challenge_id = kwargs.pop('challenge_id', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.instance.pk:
            get_object_or_404(self.request.user.teams, pk=self.instance.id)
            challenge = self.instance.challenge
        else:
            challenge = get_object_or_404(Challenge.objects, id=self.challenge_id)
            if self.task_id:
                get_object_or_404(Task.objects.filter(challenge=challenge), pk=self.task_id)

        # Unique together constraints don't provide validation out of the box
        if Team.objects.filter(name=self.cleaned_data['name'], challenge=challenge).exists():
            raise ValidationError(
                f'A team with this name already exists for the {challenge.name} challenge.'
            )

        if challenge.locked:
            raise ValidationError(f'The {challenge.name} challenge is locked.')

    def get_invites(self):
        for field in range(3):
            if self.cleaned_data[f'initial_invite_{field + 1}']:
                yield TeamInvitation(
                    sender=self.request.user,
                    team=self.instance,
                    recipient=self.cleaned_data[f'initial_invite_{field + 1}'].lower(),
                )


class CreateSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = [
            'accepted_terms',
            'test_prediction_file',
            'creator_fingerprint_id',
        ]
        widgets = {
            'creator_fingerprint_id': forms.HiddenInput(),
        }

        error_messages = {
            'test_prediction_file': {'required': _('You must provide a prediction file.')}
        }

    def __init__(self, *args, **kwargs):
        self.approach_id = kwargs.pop('approach_id', None)
        self.request = kwargs.pop('request', None)

        super().__init__(*args, **kwargs)

        self.fields['test_prediction_file'].widget.attrs.update({'class': 'file-input'})

    def clean_accepted_terms(self):
        data = self.cleaned_data['accepted_terms']
        if not data:
            raise forms.ValidationError('You must accept the data sharing policy terms.')

        return data

    def clean_test_prediction_file(self):
        actual_extension = (
            PurePath(self.cleaned_data['test_prediction_file'].name).suffix[1:].lower()
        )
        expected_extension = self.instance.approach.task.allowed_submission_extension

        if actual_extension != expected_extension:
            raise ValidationError(f'Prediction file must be of type {expected_extension}.')

        return self.cleaned_data['test_prediction_file']

    def clean(self):
        super().clean()

        if not self.request.user.has_perm(
            'approaches.add_submission', Approach.objects.get(pk=self.approach_id)
        ):
            raise ValidationError("You don't have permissions to do that.")

        if self.cleaned_data['creator_fingerprint_id']:
            banned_submissions_matching_fingerprint = Submission.objects.exclude(
                creator=self.request.user
            ).filter(
                creator_fingerprint_id=self.cleaned_data['creator_fingerprint_id'],
                creator__is_active=False,
            )

            if banned_submissions_matching_fingerprint.exists():
                ip = self.request.headers.get('x-forwarded-for', '').split(',')[0]
                logger.info(
                    f'Denied user submission for uid={self.request.user.id} fp={self.cleaned_data["creator_fingerprint_id"]} ip={ip}'  # noqa: E501
                )
                raise ValidationError('Your account has been flagged for abuse.')


class ApproachForm(forms.ModelForm):
    class Meta:
        model = Approach
        fields = ['name', 'description', 'uses_external_data', 'manuscript', 'docker_tag']
        widgets = {'uses_external_data': forms.RadioSelect}

        error_messages = {'manuscript': {'required': _('You must provide a manuscript file.')}}

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.instance = kwargs.get('instance', None)
        self.team_id = kwargs.pop('team_id', None)
        self.task_id = kwargs.pop('task_id', None)
        super().__init__(*args, **kwargs)

        self.fields['manuscript'].widget.attrs.update({'class': 'file-input'})

        task = get_object_or_404(Task, pk=self.task_id)
        # if the approach is being created and the task indicates a manuscript is required
        if self.instance.pk is None and task.requires_manuscript:
            self.fields['manuscript'].required = True
            # The widget must be explicitly updated, since it already was instantiated
            self.fields['manuscript'].widget.is_required = True

    def clean_description(self):
        # We can't put this in the model layer since the description field was introduced
        # after approaches existed.
        if self.cleaned_data['description'].strip() == '':
            raise ValidationError('This field is required.')
        else:
            return self.cleaned_data['description']

    def clean(self):
        super().clean()
        if self.instance.pk:
            team = self.instance.team
            task = self.instance.task
            get_object_or_404(
                Approach.objects.filter(team__users=self.request.user), pk=self.instance.id
            )
        else:
            team = get_object_or_404(self.request.user.teams, pk=self.team_id)
            task = get_object_or_404(Task, pk=self.task_id)

            if (
                task.max_approaches != 0
                and Approach.objects.filter(team=team, task=task).count() >= task.max_approaches
            ):
                raise ValidationError(
                    f"You\'ve reached the maximum number of approaches for {task.name}."
                )

        # Unique together constraints don't provide validation out of the box
        duplicate_name_approaches = Approach.objects.filter(
            name=self.cleaned_data['name'], task=task, team=team
        )
        if self.instance.pk:
            duplicate_name_approaches = duplicate_name_approaches.exclude(pk=self.instance.id)
        if duplicate_name_approaches.exists():
            raise ValidationError(
                f'An approach with this name already exists for the {task.name} task.'
            )

        if task.locked:
            raise ValidationError(f'The task {task.name} is locked.')
