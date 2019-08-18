from django.urls import reverse
import pytest

from core.tests.factories import TaskFactory


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
