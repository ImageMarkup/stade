import pytest

from core.tests.factories import ApproachFactory, SubmissionFactory, TaskFactory, TeamFactory


@pytest.fixture
def task_with_submissions():
    """
    this is designed to return a set of teams, approaches, and submissions to a task that
    will exercise edge cases that the leaderboard should correctly handle, namely:

    - a team and approach with no submissions at all (t2)
    - an approach where the most recent submission has failed (t0_a0)
    - an approach where the most recent score is worse than a prior score (t1_a0)

    """
    task = TaskFactory(challenge__name='Test Challenge', name='Test Task', scores_published=True)

    teams = [
        TeamFactory(challenge=task.challenge),
        TeamFactory(challenge=task.challenge),
        TeamFactory(challenge=task.challenge),
    ]

    t0_a0 = ApproachFactory(task=task, team=teams[0], name='approach_0')
    SubmissionFactory(approach=t0_a0, status='succeeded', overall_score=0.90)
    SubmissionFactory(approach=t0_a0, status='succeeded', overall_score=0.95)
    SubmissionFactory(approach=t0_a0, status='failed')

    t0_a1 = ApproachFactory(task=task, team=teams[0], name='approach_1')
    SubmissionFactory(approach=t0_a1, status='succeeded', overall_score=0.80)

    t1_a0 = ApproachFactory(task=task, team=teams[1], name='approach_0')
    SubmissionFactory(approach=t1_a0, status='succeeded', overall_score=0.82)
    SubmissionFactory(approach=t1_a0, status='succeeded', overall_score=0.78)

    t2_a0 = ApproachFactory(task=task, team=teams[2], name='approach_0')  # noqa
    # intentionally no associated submissions

    yield task


@pytest.mark.django_db
def test_leaderboard_by_approach(task_with_submissions, client):
    resp = client.get(f'/api/leaderboard/{task_with_submissions.id}/by-approach')
    assert resp.status_code == 200

    # assert the by approach leaderboard looks like
    # team0 | approach0 | .95
    # team0 | approach1 | .80
    # team1 | approach1 | .78
    first, second, third = resp.json()['results']

    assert first['team_name'] == 'team_0'
    assert first['approach_name'] == 'approach_0'
    assert first['overall_score'] == 0.95
    assert second['team_name'] == 'team_0'
    assert second['approach_name'] == 'approach_1'
    assert second['overall_score'] == 0.80
    assert third['team_name'] == 'team_1'
    assert third['approach_name'] == 'approach_0'
    assert third['overall_score'] == 0.78


@pytest.mark.django_db
def test_leaderboard_by_team(task_with_submissions, client):
    resp = client.get(f'/api/leaderboard/{task_with_submissions.id}/by-team')
    assert resp.status_code == 200

    # assert the by team leaderboard looks like
    # team3 | approach0 | .95
    # team4 | approach0 | .78
    first, second = resp.json()['results']

    assert first['team_name'] == 'team_3'
    assert first['approach_name'] == 'approach_0'
    assert first['overall_score'] == 0.95
    assert second['team_name'] == 'team_4'
    assert second['approach_name'] == 'approach_0'
    assert second['overall_score'] == 0.78
