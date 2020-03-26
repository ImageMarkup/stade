import math
import os

from django.utils.dateparse import parse_datetime
import pytest
import requests


@pytest.mark.parametrize(
    'stade_id, covalic_id',
    [
        (37, '566744dccad3a56fac786787'),
        (38, '56674518cad3a56fac78678c'),
        (40, '56fc26f7cad3a54f8bb80e4c'),
        (39, '5667455bcad3a56fac786791'),
        (41, '56fc2763cad3a54f8bb80e51'),
        (42, '584b0afacad3a51cc66c8e24'),
        (43, '584b0afacad3a51cc66c8e2e'),
        (44, '584b0afccad3a51cc66c8e38'),
        (45, '5b1c193356357d41064da2ec'),
        (46, '5b1c1a9f56357d41064da2f6'),
        (47, '5b1c1aa756357d41064da300'),
    ],
    ids=[
        '2016.1',
        '2016.2',
        '2016.2b',
        '2016.3',
        '2016.3b',
        '2017.1',
        '2017.2',
        '2017.3',
        '2018.1',
        '2018.2',
        '2018.3',
    ],
)
def test_leaderboard_responses(stade_id, covalic_id):
    expected = requests.get(
        f'https://challenge.kitware.com/api/v1/covalic_submission?limit=0&offset=0&sort=overallScore&sortdir=-1&phaseId={covalic_id}',  # noqa
        headers={'girder-token': os.getenv('GIRDER_TOKEN')},
    ).json()

    actual = requests.get(
        f'http://127.0.0.1:8000/api/leaderboard/{stade_id}/by-approach?limit=0'
    ).json()['results']

    actual = sorted(actual, key=lambda x: x['submission_created'])
    expected = sorted(expected, key=lambda x: x['created'])

    assert len(actual) == len(expected)

    for a, e in zip(actual, expected):
        assert a['approach_name'] == e['title'] or a['approach_name'] == e['approach']
        assert parse_datetime(a['submission_created']) == parse_datetime(e['created'])
        assert math.isclose(a['overall_score'], e['overallScore'])

        # 2017 checks
        if stade_id in [42, 43, 44]:
            assert a['approach_manuscript_url']
            assert a['team_institution_name'] == e['organization']

            if a['team_institution_url']:
                assert a['team_institution_url'] == e['organizationUrl']

        # TODO: test submission and manuscript files?

        if stade_id in [45, 46, 47]:
            assert a['approach_manuscript_url']
            assert a['team_institution_name'] == e['organization']

            if a['team_institution_url']:
                assert a['team_institution_url'] == e['organizationUrl']

            assert a['approach_uses_external_data'] == e['meta']['usesExternalData']
