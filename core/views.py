import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
import requests
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.pagination import LimitOffsetPagination
from rules.contrib.views import objectgetter, permission_required

from core.forms import (
    AcceptInvitationForm,
    ApproachForm,
    CreateInvitationForm,
    CreateSubmissionForm,
    ReviewApproachForm,
    TeamForm,
)
from core.leaderboard import submissions_by_approach, submissions_by_team
from core.models import (
    Approach,
    Challenge,
    Submission,
    SubmissionApproach,
    Task,
    Team,
    TeamInvitation,
)
from core.serializers import LeaderboardEntrySerializer
from core.tasks import generate_submission_bundle, score_submission, send_team_invitation
from core.utils import safe_redirect


logger = logging.getLogger(__name__)


def handler500(request):
    return render(request, 'errors/application-error.html', status=500)


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
def leaderboard(request, task_id, cluster):
    if request.user.is_staff:
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


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
def submission_scores(request, submission_id):
    if request.user.is_staff:
        # Remove all deferred fields, since we want the score immediately
        submission = get_object_or_404(Submission.objects.defer(None), pk=submission_id)
    else:
        # Remove all deferred fields, since we want the score immediately
        submission = get_object_or_404(
            Submission.objects.defer(None).filter(approach__task__scores_published=True),
            pk=submission_id,
        )

    return JsonResponse(submission.score)


def index(request):
    challenges = Challenge.objects.prefetch_related('tasks')

    # for users, only show challenges with > 0 non-hidden tasks
    if not request.user.is_superuser:
        challenges = challenges.annotate(
            num_visible_tasks=Count('tasks', filter=Q(tasks__hidden=False))
        ).filter(num_visible_tasks__gt=0)

    return render(request, 'index.html', {'challenges': challenges.all()})


@user_passes_test(lambda u: u.is_staff)
def review_approaches(request, task_id):
    task = get_object_or_404(Task.objects, pk=task_id)
    approaches = []
    reviewed_approaches = []

    all_approaches = task.approach_set(manager='successful').select_related('team').order_by('name')
    relevant_submissions = SubmissionApproach.index_by_approach(
        SubmissionApproach.objects.select_related('submission', 'approach').filter(
            approach__in=all_approaches
        )
    )

    for approach in all_approaches:
        approach.relevant_submission = relevant_submissions[approach.id].submission

        if approach.review_state == '':
            approaches.append(approach)
        else:
            reviewed_approaches.append(approach)

    return render(
        request,
        'staff/review-approaches.html',
        {
            'task': task,
            'approaches': approaches,
            'form': ReviewApproachForm(request=request),
            'reviewed_approaches': reviewed_approaches,
        },
    )


@user_passes_test(lambda u: u.is_staff)
@require_http_methods(['POST'])
def submit_approach_review(request, approach_id):
    approach = get_object_or_404(Approach, pk=approach_id)
    form = ReviewApproachForm(request.POST, request=request)

    if form.is_valid():
        with transaction.atomic():
            approach.review_state = form.cleaned_data['action']
            approach.reject_reason = form.cleaned_data['reason']
            approach.review_history.create(
                reviewed_by=request.user,
                review_state=form.cleaned_data['action'],
                reject_reason=form.cleaned_data['reason'],
            )
            approach.save()

        new_status = (
            'reset' if form.cleaned_data['action'] == '' else approach.get_review_state_display()
        )

        messages.add_message(request, messages.SUCCESS, f'{approach.name} has been {new_status}.')

        return safe_redirect(request, request.GET.get('next'))
    else:
        messages.add_message(request, messages.ERROR, 'The rejection reason is required.')
        # This should never fail
        logger.error(f'Failed to submit approach review, {form.errors}')
        return safe_redirect(request, request.GET.get('next'))


@user_passes_test(lambda u: u.is_staff)
@require_http_methods(['POST'])
def request_submission_bundle(request, task_id):
    generate_submission_bundle.delay(task_id, request.user.id)
    messages.add_message(
        request,
        messages.SUCCESS,
        (
            'Preparing the submission bundle, a download link will be sent to '
            f'{request.user.email} when complete.'
        ),
    )
    return safe_redirect(request, request.GET.get('next'))


@user_passes_test(lambda u: u.is_staff)
def dashboard(request):
    context = {'num_users': User.objects.count(), 'challenges': []}

    if not settings.DEBUG:
        r = requests.get(
            f'{settings.MAILCHIMP_API_URL}/3.0/lists/{settings.MAILCHIMP_LIST_ID}',
            auth=('', settings.MAILCHIMP_API_KEY),
            headers={'Content-Type': 'application/json'},
        )
        r.raise_for_status()
        context['num_mailchimp_subscribers'] = r.json()['stats']['member_count']
    else:
        context['num_mailchimp_subscribers'] = 5000

    for challenge in Challenge.objects.exclude(name='ISIC Sandbox').all():
        context['challenges'].append(
            {
                'challenge': challenge,
                'num_teams': challenge.team_set.count(),
                'num_successful_approaches': Approach.successful.filter(
                    task__challenge=challenge
                ).count(),
                'num_total_submissions': Submission.objects.filter(
                    approach__task__challenge=challenge
                ).count(),
            }
        )

    return render(request, 'staff/dashboard.html', context)


def task_detail(request, task_id):
    task = get_object_or_404(Task.objects, pk=task_id)

    context = {'task': task}

    if request.user.is_authenticated:
        context['teams'] = request.user.teams.filter(challenge=task.challenge).prefetch_related(
            'users', 'approach_set'
        )

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
        form = TeamForm(
            request.POST, task_id=task.id, challenge_id=task.challenge_id, request=request
        )

        if form.is_valid():
            team = form.save(commit=False)
            team.creator = request.user
            team.challenge = task.challenge
            team.save()

            for invite in form.get_invites():
                invite.save()
                send_team_invitation.delay(invite.id)

            return HttpResponseRedirect(reverse('create-approach', args=[task.id, team.id]))
    else:
        form = TeamForm(task_id=task.id, request=request)

    return render(
        request,
        'wizard/create-team.html',
        {
            'show_initial_invites': True,
            'form': form,
            'task': task,
            'teams': request.user.teams.prefetch_related('users')
            .filter(challenge=task.challenge)
            .all(),
        },
    )


@login_required
def create_team_standalone(request, challenge_id):
    challenge = get_object_or_404(Challenge.objects.filter(locked=False), pk=challenge_id)

    if request.method == 'POST':
        form = TeamForm(request.POST, challenge_id=challenge.id)

        if form.is_valid():
            team = form.save(commit=False)
            team.creator = request.user
            team.challenge = challenge
            team.save()
            return safe_redirect(request, request.POST.get('next'))
    else:
        form = TeamForm(request=request, challenge_id=challenge.id)

    return render(
        request,
        'create-team.html',
        {'form': form, 'challenge': challenge, 'next': request.GET.get('next')},
    )


@login_required
def edit_team(request, team_id):
    team = get_object_or_404(request.user.teams, pk=team_id)

    if request.method == 'POST':
        form = TeamForm(request.POST, request=request, instance=team)

        if form.is_valid():
            form.save()
            return safe_redirect(request, request.POST.get('next'))
    else:
        form = TeamForm(instance=team)

    return render(
        request, 'edit-team.html', {'form': form, 'team': team, 'next': request.GET.get('next', '')}
    )


@login_required
def accept_invitation(request):
    if request.method == 'POST':
        form = AcceptInvitationForm(request.POST, request=request)

        if form.is_valid():
            invitation = get_object_or_404(TeamInvitation, pk=form.cleaned_data['invitation_id'])
            # try catch, inside transaction
            invitation.team.users.add(request.user)
            invitation.delete()
            messages.add_message(request, messages.SUCCESS, f'Welcome to {invitation.team.name}!')
            return HttpResponseRedirect(reverse('index'))
        else:
            print(form.errors)


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
                request,
                messages.SUCCESS,
                f'Successfully invited {form.cleaned_data["recipient"]} to {team.name}.',
            )
            return safe_redirect(request, request.POST.get('next'))
    else:
        form = CreateInvitationForm(request=request)

    return render(
        request,
        'create-invitation.html',
        {'form': form, 'team': team, 'next': request.GET.get('next', '')},
    )


@login_required
def create_approach(request, task_id, team_id):
    # Note: this permission checking is duplicated in the CreateApproachForm
    task = get_object_or_404(Task.objects.filter(locked=False), pk=task_id)
    team = get_object_or_404(request.user.teams, pk=team_id)

    if request.method == 'POST':
        form = ApproachForm(
            request.POST, request.FILES, request=request, task_id=task_id, team_id=team_id
        )
        form.instance.team = team
        form.instance.task = task

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('create-submission', args=[form.instance.id]))
    else:
        form = ApproachForm(request=request, task_id=task_id, team_id=team_id)

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
def edit_approach(request, approach_id):
    approach = get_object_or_404(Approach.objects.filter(team__users=request.user), pk=approach_id)

    if request.method == 'POST':
        form = ApproachForm(request.POST, request.FILES, request=request, instance=approach)

        if form.is_valid():
            form.save()
            return safe_redirect(request, request.POST.get('next'))
    else:
        form = ApproachForm(request=request, instance=approach)

    return render(
        request,
        'edit-approach.html',
        {
            'form': form,
            'task': approach.task,
            'approach': approach,
            'next': request.GET.get('next'),
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
