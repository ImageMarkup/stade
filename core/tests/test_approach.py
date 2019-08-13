import pytest

from core.models import Approach
from core.tests.factories import ApproachFactory, SubmissionFactory


@pytest.fixture
def approaches(transactional_db):
    yield [ApproachFactory(), ApproachFactory()]


def test_approach_successful_manager(approaches):
    a1, a2 = approaches

    # approaches with no submissions
    assert Approach.successful.count() == 0
    assert Approach.objects.count() == 2

    # approaches have submissions, neither have succeeded
    SubmissionFactory(status='queued', approach=a1)
    SubmissionFactory(status='failed', approach=a1)
    SubmissionFactory(status='failed', approach=a2)

    assert Approach.successful.count() == 0
    assert Approach.objects.count() == 2

    # give a2 a successful submission
    SubmissionFactory(status='succeeded', approach=a2)

    assert Approach.successful.count() == 1
    assert Approach.successful.first() == a2
    assert Approach.objects.count() == 2
