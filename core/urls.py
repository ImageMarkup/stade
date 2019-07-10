from django.urls import path

from core.views import CreateApproachView
from . import views
from .views import AcceptInvitationView


urlpatterns = [
    path('', views.index, name='index'),
    path('task/<int:task_id>', views.task_detail, name='task-detail'),
    path('submission/<int:submission_id>', views.submission_detail, name='submission-detail'),
    path('submissions/<int:task_id>/<int:team_id>', views.submission_list, name='submission-list'),
    path('team-invite/accept', AcceptInvitationView.as_view(), name='accept-invitation'),
    # wizard
    path('create-team/<int:task>', views.create_team, name='create-team'),
    path(
        'create-approach/<int:task>/<int:team>',
        CreateApproachView.as_view(),
        name='create-approach',
    ),
    path('create-submission/<int:approach>', views.create_submission, name='create-submission'),
    path(
        'api/leaderboard/<int:task_id>/by-approach',
        views.leaderboard,
        {'cluster': 'approach'},
        name='leaderboard-by-approach',
    ),
    path(
        'api/leaderboard/<int:task_id>/by-team',
        views.leaderboard,
        {'cluster': 'team'},
        name='leaderboard-by-team',
    ),
]
