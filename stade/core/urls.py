from django.urls import path
from django.views.generic import TemplateView

from stade.core import views
from stade.core.rest import views as api_views

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('task/<int:task_id>', views.task_detail, name='task-detail'),
    path('submission/<int:submission_id>', views.submission_detail, name='submission-detail'),
    path('submissions/<int:task_id>/<int:team_id>', views.submission_list, name='submission-list'),
    path('team-invite/accept', views.accept_invitation, name='accept-invitation'),
    # wizard
    path('create-team/<int:task>', views.create_team, name='create-team'),
    path(
        'create-approach/<int:task_id>/<int:team_id>', views.create_approach, name='create-approach'
    ),
    path('create-submission/<int:approach_id>', views.create_submission, name='create-submission'),
    path('create-invitation/<int:team_id>', views.create_invitation, name='create-invitation'),
    path(
        'team/create/<int:challenge_id>',
        views.create_team_standalone,
        name='create-team-standalone',
    ),
    path('edit-team/<int:team_id>', views.edit_team, name='edit-team'),
    path('edit-approach/<int:approach_id>', views.edit_approach, name='edit-approach'),
    path('staff/dashboard', views.dashboard, name='staff-dashboard'),
    path(
        'staff/review-approaches/<int:task_id>',
        views.review_approaches,
        name='staff-review-approaches',
    ),
    path(
        'staff/review/<int:approach_id>',
        views.submit_approach_review,
        name='submit-approach-review',
    ),
    path(
        'staff/request-submission-bundle/<int:task_id>',
        views.request_submission_bundle,
        name='request-submission-bundle',
    ),
    path('api/challenge/<int:challenge_id>', api_views.challenge_detail, name='challenge-detail'),
    path(
        'api/leaderboard/<int:task_id>/by-approach',
        api_views.leaderboard,
        {'cluster': 'approach'},
        name='leaderboard-by-approach',
    ),
    path(
        'api/leaderboard/<int:task_id>/by-team',
        api_views.leaderboard,
        {'cluster': 'team'},
        name='leaderboard-by-team',
    ),
    path(
        'api/submission/<int:submission_id>/score',
        api_views.submission_scores,
        name='submission-scores',
    ),
    path('data', TemplateView.as_view(template_name='data.html'), name='data'),
    path('challenges', views.challenges, name='challenges'),
    path('leaderboards/<challenge_nicename>', views.leaderboard_page, name='leaderboards'),
    path('landing/<challenge_nicename>', views.challenge_landing, name='challenge-landing'),
    path('landing/<challenge_nicename>/<int:task_id>', views.task_landing, name='task-landing'),
    path(
        'terms-of-use', TemplateView.as_view(template_name='terms-of-use.html'), name='terms-of-use'
    ),
]

handler500 = views.handler500
