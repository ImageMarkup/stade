import pytest

from stade.core.models import Approach, Submission


@pytest.fixture
def task_with_submissions(db, approach_factory, submission_factory, task_factory, team_factory):
    """
    Return a set of teams, approaches, and submissions to a task to exercise edge cases.

    Namely, this includes:
    - a team and approach with no submissions at all (t2)
    - an approach where the most recent submission has failed (t0_a0)
    - an approach where the most recent score is worse than a prior score (t1_a0)
    - a team with a better approach which has been rejected (t3)
    """
    task = task_factory(challenge__name='Test Challenge', name='Test Task', scores_published=True)

    teams = [
        team_factory(challenge=task.challenge),
        team_factory(challenge=task.challenge),
        team_factory(challenge=task.challenge),
        team_factory(challenge=task.challenge),
    ]

    t0_a0 = approach_factory(task=task, team=teams[0], name='approach_0')
    submission_factory(approach=t0_a0, status=Submission.Status.SUCCEEDED, overall_score=0.90)
    submission_factory(approach=t0_a0, status=Submission.Status.SUCCEEDED, overall_score=0.95)
    submission_factory(approach=t0_a0, status=Submission.Status.FAILED)

    t0_a1 = approach_factory(task=task, team=teams[0], name='approach_1')
    submission_factory(approach=t0_a1, status=Submission.Status.SUCCEEDED, overall_score=0.80)

    t1_a0 = approach_factory(
        task=task, team=teams[1], name='approach_0', review_state=Approach.ReviewState.ACCEPTED
    )
    submission_factory(approach=t1_a0, status=Submission.Status.SUCCEEDED, overall_score=0.82)
    submission_factory(approach=t1_a0, status=Submission.Status.SUCCEEDED, overall_score=0.78)

    t2_a0 = approach_factory(task=task, team=teams[2], name='approach_0')  # noqa
    # intentionally no associated submissions

    t3_a0 = approach_factory(
        task=task, team=teams[3], name='approach_0', review_state=Approach.ReviewState.REJECTED
    )
    submission_factory(approach=t3_a0, status=Submission.Status.SUCCEEDED, overall_score=1.0)

    t3_a1 = approach_factory(
        task=task, team=teams[3], name='approach_1', review_state=Approach.ReviewState.ACCEPTED
    )
    submission_factory(approach=t3_a1, status=Submission.Status.SUCCEEDED, overall_score=0.60)

    return task


@pytest.mark.django_db
def test_leaderboard_by_approach(task_with_submissions, client):
    resp = client.get(f'/api/leaderboard/{task_with_submissions.id}/by-approach')
    assert resp.status_code == 200

    # assert the by approach leaderboard looks like
    # team0 | approach0 | .95
    # team0 | approach1 | .80
    # team1 | approach1 | .78
    # team3 | approach1 | .60
    first, second, third, fourth = resp.json()['results']

    assert first['team_name'] == 'team_0'
    assert first['approach_name'] == 'approach_0'
    assert first['overall_score'] == 0.95
    assert second['team_name'] == 'team_0'
    assert second['approach_name'] == 'approach_1'
    assert second['overall_score'] == 0.80
    assert third['team_name'] == 'team_1'
    assert third['approach_name'] == 'approach_0'
    assert third['overall_score'] == 0.78
    assert fourth['team_name'] == 'team_3'
    assert fourth['approach_name'] == 'approach_1'
    assert fourth['overall_score'] == 0.60


@pytest.mark.django_db
def test_leaderboard_by_team(task_with_submissions, client):
    resp = client.get(f'/api/leaderboard/{task_with_submissions.id}/by-team')
    assert resp.status_code == 200

    # assert the by team leaderboard looks like
    # team4 | approach0 | .95
    # team5 | approach0 | .78
    # team7 | approach1 | .60
    first, second, third = resp.json()['results']

    assert first['team_name'] == 'team_4'
    assert first['approach_name'] == 'approach_0'
    assert first['overall_score'] == 0.95
    assert second['team_name'] == 'team_5'
    assert second['approach_name'] == 'approach_0'
    assert second['overall_score'] == 0.78
    assert third['team_name'] == 'team_7'
    assert third['approach_name'] == 'approach_1'
    assert third['overall_score'] == 0.60
