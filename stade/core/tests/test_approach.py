import pytest

from stade.core.models import Approach, Submission


@pytest.mark.django_db(transaction=True)
def test_approach_successful_manager(approach_factory, submission_factory):
    a1 = approach_factory()
    a2 = approach_factory()

    # approaches with no submissions
    assert Approach.successful.count() == 0
    assert Approach.objects.count() == 2

    # approaches have submissions, neither have succeeded
    submission_factory(status=Submission.Status.QUEUED, approach=a1)
    submission_factory(status=Submission.Status.FAILED, approach=a1)
    submission_factory(status=Submission.Status.FAILED, approach=a2)

    assert Approach.successful.count() == 0
    assert Approach.objects.count() == 2

    # give a2 a successful submission
    submission_factory(status=Submission.Status.SUCCEEDED, approach=a2)

    assert Approach.successful.count() == 1
    assert Approach.successful.first() == a2
    assert Approach.objects.count() == 2
