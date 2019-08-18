from django.urls import reverse
import pytest

from core.tests.factories import ApproachFactory, SubmissionFactory, TaskFactory, TeamFactory


@pytest.fixture
def user(django_user_model, transactional_db):
    u = django_user_model.objects.create_user(
        username='someone', email='someone@something.com', password='something'
    )
    yield u


@pytest.fixture
def staff_user(django_user_model, transactional_db):
    u = django_user_model.objects.create_user(
        username='staff1', email='staff1@something.com', password='something'
    )
    u.is_staff = True
    u.save()
    yield u


def test_index_is_public(transactional_db, client):
    r = client.get('/')
    assert r.status_code == 200


def test_task_detail_hidden(transactional_db, client):
    task = TaskFactory(hidden=False)
    task.save()
    r = client.get(reverse('task-detail', args=[task.id]))
    assert r.status_code == 200

    task.hidden = True
    task.save()
    r = client.get(reverse('task-detail', args=[task.id]), follow=True)
    assert r.status_code == 403


def test_submission_detail_hidden(transactional_db, client, user):
    assert client.login(username='someone', password='something')

    task = TaskFactory()
    team = TeamFactory(challenge=task.challenge)

    t0_a0 = ApproachFactory(task=task, team=team)
    submission = SubmissionFactory(approach=t0_a0, status='succeeded', overall_score=0.90)

    r = client.get(reverse('submission-detail', args=[submission.id]), follow=True)
    assert r.status_code == 403

    team.user_set.add(user)
    r = client.get(reverse('submission-detail', args=[submission.id]))
    assert r.status_code == 200
