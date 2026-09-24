from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from django.utils.dateformat import format as date_format
import pytest


@pytest.mark.django_db
def test_stats_task_submission_timespan(client, task_factory, submission_factory):
    locked_task = task_factory(locked=True)
    open_task = task_factory(locked=False)
    empty_task = task_factory()

    first = submission_factory(approach__task=locked_task)
    first.created = timezone.now() - timedelta(days=400)
    first.save()
    last = submission_factory(approach__task=locked_task)
    open_submission = submission_factory(approach__task=open_task)

    stats = {t.id: t for t in locked_task.challenge.stats['tasks']}
    assert stats[locked_task.id].first_submission == first.created
    assert stats[locked_task.id].last_submission == last.created

    def month(dt):
        return date_format(timezone.localtime(dt), 'M Y')

    resp = client.get(reverse('stats'))
    assert resp.status_code == 200
    content = resp.content.decode()

    assert f'({month(first.created)} - {month(last.created)})' in content
    assert f'({month(open_submission.created)} - Present)' in content
    assert content.count('class="submission-timespan"') == 2
    assert empty_task.name in content
