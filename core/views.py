from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.db.models import Count, Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic.edit import CreateView, FormView
from rest_framework.decorators import api_view
from rest_framework.pagination import LimitOffsetPagination
from rules.contrib.views import permission_required, objectgetter

from core.forms import (
    AcceptInvitationForm,
    CreateApproachForm,
    CreateInvitationForm,
    CreateSubmissionForm,
    CreateTeamForm,
)
from core.leaderboard import submissions_by_approach, submissions_by_team
from core.models import Approach, Challenge, Submission, Task, Team, TeamInvitation
from core.serializers import LeaderboardEntrySerializer
from core.tasks import score_submission, send_team_invitation


@api_view(['GET'])
def leaderboard(request, task_id, cluster):
    if request.user.is_superuser:
        task = get_object_or_404(Task, pk=task_id)
    else:
        task = get_object_or_404(Task.objects.filter(scores_published=True), pk=task_id)

    paginator = LimitOffsetPagination()
    paginator.default_limit = paginator.max_limit = 100

    if cluster == 'approach':
        submission_ids = submissions_by_approach(task.id)
    elif cluster == 'team':
        submission_ids = submissions_by_team(task.id)
    else:
        raise Http404()

    leaderboard_submissions = (
        Submission.objects.select_related('approach', 'approach__team')
        .filter(id__in=submission_ids)
        .order_by('-overall_score', 'created')
    )

    result_page = paginator.paginate_queryset(leaderboard_submissions, request)
    serializer = LeaderboardEntrySerializer(result_page, many=True, context={'request': request})

    return paginator.get_paginated_response(serializer.data)


def index(request):
    challenges = Challenge.objects.prefetch_related('tasks')

    # for users, only show challenges with > 0 non-hidden tasks
    if not request.user.is_superuser:
        challenges = challenges.annotate(
            num_visible_tasks=Count('tasks', filter=Q(tasks__hidden=False))
        ).filter(num_visible_tasks__gt=0)

    return render(request, 'index.html', {'challenges': challenges.all()})


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task.objects, pk=task_id)

    context = {
        'task': task,
        'teams': request.user.teams.filter(challenge=task.challenge).prefetch_related(
            'users', 'approach_set'
        ),
    }

    return render(request, 'task-detail.html', context)


@login_required
def submission_detail(request, submission_id):
    submission = Submission.objects.select_related('approach', 'approach__task', 'approach__team')

    if not request.user.is_superuser:
        submission = submission.filter(approach__team_id__in=request.user.teams.only('id'))

    submission = get_object_or_404(submission, pk=submission_id)

    return render(request, 'submission-detail.html', {'submission': submission})


@login_required
def submission_list(request, task_id, team_id):
    if request.user.is_superuser:
        task = get_object_or_404(Task, pk=task_id)
        team = get_object_or_404(Team, pk=team_id)
    else:
        task = get_object_or_404(Task.objects.filter(hidden=False), pk=task_id)
        team = get_object_or_404(request.user.teams, pk=team_id)

    submissions = (
        Submission.objects.filter(approach__team=team, approach__task=task)
        .select_related('approach')
        .all()
    )

    return render(
        request, 'submission-list.html', {'task': task, 'team': team, 'submissions': submissions}
    )


@login_required
def create_team(request, task):
    # Note: this permission checking is duplicated in the CreateTeamForm
    task = get_object_or_404(Task.objects.filter(challenge__locked=False), pk=task)

    if request.method == 'POST':
        form = CreateTeamForm(request.POST, task_id=task.id)

        if form.is_valid():
            team = form.save(commit=False)
            team.creator = request.user
            team.challenge = task.challenge
            team.save()
            return HttpResponseRedirect(reverse('create-approach', args=[task.id, team.id]))
    else:
        form = CreateTeamForm(task_id=task.id)

    return render(
        request,
        'wizard/create-team.html',
        {
            'form': form,
            'task': task,
            'teams': request.user.teams.prefetch_related('users')
            .filter(challenge=task.challenge)
            .all(),
        },
    )


class AcceptInvitationView(LoginRequiredMixin, FormView):
    template_name = 'contact.html'  # fix, unused
    form_class = AcceptInvitationForm

    def get_success_url(self):
        return reverse('index')  # todo redirect to correct task

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs(), request=self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

    def form_valid(self, form):
        # add user to team, delete invitation
        team_invitation = get_object_or_404(TeamInvitation, pk=form.cleaned_data['invitation_id'])

        # try catch, inside transaction
        team_invitation.team.users.add(team_invitation.recipient)
        team_invitation.delete()
        return super().form_valid(form)


@login_required
def create_invitation(request, team_id):
    team = get_object_or_404(request.user.teams, pk=team_id)

    if request.method == 'POST':
        form = CreateInvitationForm(request.POST, request=request, team_id=team_id)

        if form.is_valid():
            invite = form.save(commit=False)
            invite.team = team
            invite.sender = request.user
            invite.save()
            send_team_invitation.delay(invite.id)
            messages.add_message(
                request, messages.SUCCESS, f'Successfully invited {form.cleaned_data["recipient"]}'
            )
            return HttpResponseRedirect(reverse('index'))
    else:
        form = CreateInvitationForm(request=request)

    return render(request, 'create-invitation.html', {'form': form, 'team': team})


@login_required
def create_approach(request, task_id, team_id):
    # Note: this permission checking is duplicated in the CreateApproachForm
    task = get_object_or_404(Task.objects.filter(locked=False), pk=task_id)
    team = get_object_or_404(request.user.teams, pk=team_id)

    if request.method == 'POST':
        form = CreateApproachForm(
            request.POST, request.FILES, request=request, task_id=task_id, team_id=team_id
        )
        form.instance.team = team
        form.instance.task = task

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('create-submission', args=[form.instance.id]))
    else:
        form = CreateApproachForm(request=request, task_id=task_id, team_id=team_id)

    return render(
        request,
        'wizard/create-approach.html',
        {
            'form': form,
            'task': task,
            'team': team,
            'existing_approaches': Approach.objects.filter(team=team, task=task),
        },
    )


@login_required
@permission_required('approaches.add_submission', fn=objectgetter(Approach, 'approach_id'))
def create_submission(request, approach_id):
    approach = get_object_or_404(Approach, pk=approach_id)

    if request.method == 'POST':
        form = CreateSubmissionForm(
            request.POST, request.FILES, approach_id=approach_id, request=request
        )
        # TODO: Is this the proper way to set these?
        form.instance.approach = approach
        form.instance.creator = request.user

        if form.is_valid():
            form.save()
            score_submission.delay(form.instance.id)
            return HttpResponseRedirect(reverse('submission-detail', args=[form.instance.id]))
    else:
        form = CreateSubmissionForm(approach_id=approach_id, request=request)

    return render(request, 'wizard/create-submission.html', {'form': form, 'approach': approach})
