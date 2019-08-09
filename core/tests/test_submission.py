from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.utils import timezone
import pytest

from core.forms import CreateSubmissionForm
from core.tests.factories import ApproachFactory, SubmissionFactory


@pytest.fixture
def approach(transactional_db):
    a = ApproachFactory(task__max_submissions_per_week=1, task__locked=False)
    # this object must be saved because we need an id to submit the form
    a.save()

    # add user to team
    a.team.users.add(a.team.creator)

    yield a


def test_submission_throttling(approach):
    request = HttpRequest()
    request.user = approach.team.creator

    for _ in range(approach.task.max_submissions_per_week):
        form = CreateSubmissionForm(
            data={'accepted_terms': True},
            files={'test_prediction_file': SimpleUploadedFile('some-file.csv', b'foo')},
            approach_id=approach.id,
            request=request,
        )
        form.instance.approach = approach
        form.instance.creator = approach.team.creator
        assert form.is_valid(), form.errors
        form.save()

    form = CreateSubmissionForm(
        data={'accepted_terms': True},
        files={'test_prediction_file': SimpleUploadedFile('some-file.csv', b'foo')},
        approach_id=approach.id,
        request=request,
    )
    form.instance.approach = approach
    form.instance.creator = approach.team.creator
    assert not form.is_valid(), form.errors


def test_next_available_submission(approach):
    start = timezone.now()
    submission_creation_time = start - timedelta(days=1)

    SubmissionFactory(created=submission_creation_time, approach=approach)

    # The approach should now be rate limited
    assert (
        approach.task.pending_or_succeeded_submissions(approach.team).count()
        == approach.task.max_submissions_per_week
    )

    # The next available submission should be in 6 days
    assert approach.task.next_available_submission(
        approach.team
    ) == submission_creation_time + timedelta(weeks=1)
