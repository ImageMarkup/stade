from django.http import HttpResponseRedirect

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.db.models import Count, Q, Prefetch, Max
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from core.forms import (
    AcceptInvitationForm,
    CreateApproachForm,
    CreateSubmissionForm,
    CreateTeamForm,
)
from core.models import Approach, Challenge, Submission, Task, Team, TeamInvitation
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, FormView


def index(request):
    challenges = Challenge.objects.filter(active=True)

    # for admins, show challenges with > 0 tasks,
    # for users, only show challenges with > 0 public tasks
    if request.user.is_staff:
        challenges = challenges.annotate(num_tasks=Count('tasks')).filter(num_tasks__gt=0)
    else:
        challenges = challenges.annotate(
            num_public_tasks=Count("tasks", filter=Q(tasks__public=True))
        ).filter(num_public_tasks__gt=0)

    return render(request, "index.html", {"challenges": challenges.all()})


class AcceptInvitationView(LoginRequiredMixin, FormView):
    template_name = "contact.html"  # fix, unused
    form_class = AcceptInvitationForm

    def get_success_url(self):
        return reverse("index")  # todo redirect to correct task

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs(), request=self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context

    def form_valid(self, form):
        # add user to team, delete invitation
        team_invitation = get_object_or_404(TeamInvitation, pk=form.cleaned_data["invitation_id"])

        # try catch, inside transaction
        team_invitation.team.users.add(team_invitation.recipient)
        team_invitation.delete()
        return super().form_valid(form)


class SubmissionDetail(LoginRequiredMixin, DetailView):
    model = Submission
    template_name = 'submission-detail.html'

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset


@login_required
def task_detail(request, task):
    task = get_object_or_404(Task.objects.select_related('challenge'), pk=task)
    context = {
        'task': task,
        'teams': request.user.teams.filter(challenge=task.challenge).prefetch_related(
            'users', 'approach_set'
        ),
    }

    return render(request, 'task-detail.html', context)


from .tasks import score_submission


@login_required
def create_team(request, task):
    task = get_object_or_404(Task, pk=task)

    if request.method == 'POST':
        form = CreateTeamForm(request.POST)

        if form.is_valid():
            team = form.save(commit=False)
            team.creator = request.user
            team.challenge = task.challenge
            team.save()
            return HttpResponseRedirect(reverse('create-approach', args=[task.id, team.id]))
    else:
        form = CreateTeamForm()

    return render(request, 'wizard/create-team.html', {'form': form, 'task': task})


class CreateApproachPermissionMixin(AccessMixin):
    """Verify that the current user is a member of the 'team' kwarg."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        try:
            request.user.teams.get(pk=kwargs['team'])
        except Team.DoesNotExist:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class CreateApproachView(CreateApproachPermissionMixin, CreateView):
    form_class = CreateApproachForm
    template_name = "wizard/create-approach.html"

    def form_valid(self, form):
        team = get_object_or_404(Team, pk=self.kwargs["team"])
        task = get_object_or_404(Task, pk=self.kwargs["task"])
        approach = form.save(commit=False)
        approach.team = team
        approach.task = task
        approach.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("create-submission", args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = get_object_or_404(Team, pk=self.kwargs["team"])
        context["task"] = get_object_or_404(Task, pk=self.kwargs["task"])
        context["existing_approaches"] = Approach.objects.filter(team=context["team"])
        return context

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(
            **self.get_form_kwargs(), request=self.request, team_id=self.kwargs['team']
        )


class SubmissionListView(ListView):
    template_name = "submission-list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = self.team
        context["task"] = self.task
        return context

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        self.task = get_object_or_404(Task, pk=kwargs['task'])
        self.team = get_object_or_404(Team, pk=kwargs['team'])

        if self.team not in request.user.teams.all():
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Submission.objects.filter(approach__team=self.team)


@login_required
def create_submission(request, approach):
    approach = get_object_or_404(Approach, pk=approach)

    if not request.user.teams.filter(pk=approach.team.id).exists():
        raise Http404()

    if request.method == 'POST':
        print(request.POST)
        form = CreateSubmissionForm(request.POST, request.FILES)
        form.instance.approach = approach
        form.instance.creator = request.user

        if form.is_valid():
            form.save()
            score_submission.delay(form.instance.id)
            return HttpResponseRedirect(reverse('submission-detail', args=[form.instance.id]))
    else:
        form = CreateSubmissionForm()

    return render(request, 'wizard/create-submission.html', {'form': form, 'approach': approach})
