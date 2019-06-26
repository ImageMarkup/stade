from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from core.forms import AcceptInvitationForm, CreateApproachForm, CreateTeamForm
from core.models import Approach, Submission, Task, Team, TeamInvitation, Challenge
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, FormView


def index(request):
    challenges = Challenge.objects.filter(active=True)

    # for admins, show challenges with > 0 tasks,
    # for users, only show challenges with > 0 visible tasks
    if request.user.is_staff:
        challenges = challenges.annotate(num_tasks=Count('tasks')).filter(num_tasks__gt=0)
    else:
        challenges = challenges.annotate(
            num_visible_tasks=Count("tasks", filter=Q(tasks__visible=True))
        ).filter(num_visible_tasks__gt=0)

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

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset


class TaskDetail(DetailView):
    model = Task


class TaskDashboard(DetailView):
    model = Task
    template_name = "core/task_dashboard.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        if self.object and self.request.user.is_authenticated:
            context_data["teams"] = Team.objects.filter(
                challenge=kwargs['object'].challenge, users__in=[self.request.user]
            )
        return context_data


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

    return render(request, 'create-team.html', {'form': form, 'task': task})


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
    template_name = "create-approach.html"

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
    template_name = "core/submission-list.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        self.team = get_object_or_404(Team, pk=kwargs['team'])

        if self.team not in request.user.teams.all():
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Submission.objects.filter(approach__team=self.team)


class CreateSubmissionPermissionMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        try:
            approach = get_object_or_404(Approach, pk=self.kwargs["approach"])
            request.user.teams.get(pk=approach.team.id)
        except Team.DoesNotExist:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class CreateSubmissionView(CreateSubmissionPermissionMixin, CreateView):
    model = Submission
    fields = ["test_prediction_file"]
    template_name = "create-submission.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["approach"] = get_object_or_404(Approach, pk=self.kwargs["approach"])
        return context

    def get_success_url(self):
        return reverse("submission-detail", args=[self.object.id])

    def get(self, *args, **kwargs):
        get_object_or_404(Approach, pk=self.kwargs["approach"])
        return super().get(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.instance.approach = get_object_or_404(Approach, pk=self.kwargs["approach"])
            form.instance.task = form.instance.approach.task
            form.instance.creator = self.request.user
            self.object = form.save()
            score_submission.delay(self.object.id)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
