from . import views
from .views import AcceptInvitationView, SubmissionDetail, SubmissionListView
from core.views import CreateApproachView, CreateSubmissionView, TaskDashboard
from django.urls import path


urlpatterns = [
    path("", views.index, name="index"),
    path("task/<int:pk>", TaskDashboard.as_view(), name="task-dashboard"),
    path("submission/<int:pk>", SubmissionDetail.as_view(), name="submission-detail"),
    path("submissions/<int:task>/<int:team>", SubmissionListView.as_view(), name="submission-list"),
    path("team-invite/accept", AcceptInvitationView.as_view(), name="accept-invitation"),
    # wizard
    path("create-team/<int:task>", views.create_team, name="create-team"),
    path(
        "create-approach/<int:task>/<int:team>",
        CreateApproachView.as_view(),
        name="create-approach",
    ),
    path(
        "create-submission/<int:approach>", CreateSubmissionView.as_view(), name="create-submission"
    ),
]
