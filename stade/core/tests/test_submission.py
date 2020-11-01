from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.utils import timezone
import pytest

from stade.core.forms import CreateSubmissionForm


@pytest.fixture
def limited_approach(transactional_db, approach_factory):
    a = approach_factory(task__max_submissions_per_week=1, task__locked=False)
    # this object must be saved because we need an id to submit the form
    a.save()

    # add user to team
    a.team.users.add(a.team.creator)

    return a


@pytest.mark.django_db
def test_submission_throttling(limited_approach):
    request = HttpRequest()
    request.user = limited_approach.team.creator

    for _ in range(limited_approach.task.max_submissions_per_week):
        form = CreateSubmissionForm(
            data={'accepted_terms': True},
            files={'test_prediction_file': SimpleUploadedFile('some-file.csv', b'foo')},
            approach_id=limited_approach.id,
            request=request,
        )
        form.instance.approach = limited_approach
        form.instance.creator = limited_approach.team.creator
        assert form.is_valid(), form.errors
        form.save()

    form = CreateSubmissionForm(
        data={'accepted_terms': True},
        files={'test_prediction_file': SimpleUploadedFile('some-file.csv', b'foo')},
        approach_id=limited_approach.id,
        request=request,
    )
    form.instance.approach = limited_approach
    form.instance.creator = limited_approach.team.creator
    assert not form.is_valid(), form.errors


@pytest.mark.django_db
def test_next_available_submission(limited_approach, submission_factory):
    start = timezone.now()
    submission_creation_time = start - timedelta(days=1)

    submission_factory(created=submission_creation_time, approach=limited_approach)

    # The approach should now be rate limited
    assert (
        limited_approach.task.pending_or_succeeded_submissions(limited_approach.team).count()
        == limited_approach.task.max_submissions_per_week
    )

    # The next available submission should be in 6 days
    assert limited_approach.task.next_available_submission(
        limited_approach.team
    ) == submission_creation_time + timedelta(weeks=1)
