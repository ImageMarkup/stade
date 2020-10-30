import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from .factories import (
    ApproachFactory,
    ChallengeFactory,
    SubmissionFactory,
    TaskFactory,
    TeamFactory,
    UserFactory,
)


@pytest.fixture
def api_client():
    return APIClient()


register(ApproachFactory)
register(ChallengeFactory)
register(SubmissionFactory)
register(TaskFactory)
register(TeamFactory)
register(UserFactory)
