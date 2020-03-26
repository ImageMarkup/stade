from collections import defaultdict
from datetime import datetime
import json
import os
import re

from cachier import cachier
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
import magic
import requests

from core.models import Approach, Submission, Task, Team


def use_first_nonself_arg(*args, **kwargs):
    return args[0][1]


@cachier()
def download_file(url):
    if url.startswith('https://arxiv'):
        url = url.replace('/abs/', '/pdf/') + '.pdf'
    print(url)
    if 'challenge.kitware.com' in url:
        r = requests.get(
            url, allow_redirects=True, headers={'girder-token': os.getenv('GIRDER_TOKEN')}
        )
    else:
        r = requests.get(url, allow_redirects=True)
    r.raise_for_status()

    if 'Content-Disposition' in r.headers.keys():
        fname = re.findall('filename=(.+)', r.headers['Content-Disposition'])[0].strip('"')
    else:
        fname = url.split('/')[-1]
    content = r.content

    return content, fname


class Command(BaseCommand):
    help = 'Migrate 2017 data from Covalic'

    @cachier(hash_params=use_first_nonself_arg)
    def get_score(self, submission_id):
        r = requests.get(
            f'https://challenge.kitware.com/api/v1/covalic_submission/{submission_id}',
            headers={'Girder-Token': os.getenv('GIRDER_TOKEN')},
        )

        r.raise_for_status()
        return r.json()

    @cachier(hash_params=use_first_nonself_arg)
    def girder_user_from_id(self, user_id):
        r = requests.get(
            f'https://challenge.kitware.com/api/v1/user/{user_id}',
            headers={'Girder-Token': os.getenv('GIRDER_TOKEN')},
        )

        r.raise_for_status()
        return r.json()

    def _maybe_create_user(self, creator_id, creator_name):
        girder_user = self.girder_user_from_id(creator_id)
        user_obj = User.objects.get(email=girder_user['email'])
        created = False

        if not user_obj:
            created = True
            user_obj, _ = User.objects.create(
                username=girder_user['email'][:150],
                password='dummy',
                email=girder_user['email'],
                first_name=girder_user['first_name'][:30],
                last_name=girder_user['last_name'][:150],
                is_active=True,
                date_joined=datetime.utcfromtimestamp(girder_user['created']['$date'] / 1000),
            )
            user_obj.set_unusable_password()
            user_obj.save()

        return user_obj, created

    def _create_team(self, user, submission):
        team = Team.objects.filter(challenge_id=35, name=submission['organization']).first()
        created = False

        if not team:
            team = Team(
                challenge_id=35,
                creator=user,
                name=submission['organization'],
                institution=submission['organization'],
                institution_url=submission['organizationUrl'],
            )
            team.created = min(team.created, parse_datetime(submission['created']))
            team.save()
            created = True
        else:
            # "merge"
            if team.creator != user:
                team.users.add(user)

        return team, created

    def _create_approach(self, team, task, data):
        content, name = download_file(data['documentationUrl'])
        manuscript = SimpleUploadedFile(name, content, 'application/pdf')

        return Approach.objects.get_or_create(
            team=team,
            task=task,
            created=data['created'],
            name=data['title'],
            review_state='accepted',
            manuscript=manuscript,
        )

    def _add_submission_file(self, submission: Submission, data):
        r = requests.get(
            'https://challenge.kitware.com/api/v1/item',
            params={'folderId': data['folderId']},
            headers={'Girder-Token': os.getenv('GIRDER_TOKEN')},
        )
        r.raise_for_status()

        if len(r.json()) == 0:
            raise Exception('submission has no files')
        elif len(r.json()) == 1:
            files = requests.get(
                f'https://challenge.kitware.com/api/v1/item/{r.json()[0]["_id"]}/files',
                headers={'Girder-Token': os.getenv('GIRDER_TOKEN')},
            )
            files.raise_for_status()

            if len(files.json()) != 1:
                raise Exception('unexpected number of files')

            download_url = (
                f'https://challenge.kitware.com/api/v1/file/{files.json()[0]["_id"]}/download'
            )
        else:
            download_url = (
                f'https://challenge.kitware.com/api/v1/folder/{data["folderId"]}/download'
            )

        content, name = download_file(download_url)
        submission.test_prediction_file = SimpleUploadedFile(
            name, content, magic.from_buffer(content, mime=True)
        )
        return submission

    def handle(self, *args, **options):
        # wipe 2017 teams/approaches/submission
        Team.objects.filter(challenge_id=35).delete()

        tasks = {
            42: '2017.1.json',
            43: '2017.2.json',
            44: '2017.3.json',
        }

        for task_id, filename in tasks.items():
            counts = defaultdict(int)
            with open(filename, 'r') as data:
                data = json.loads(data.read().strip())
                assert all([x['latest'] for x in data])

                for submission in data:
                    u, created = self._maybe_create_user(
                        submission['creatorId'], submission['creatorName']
                    )
                    counts['users'] += bool(created)
                    team, created = self._create_team(u, submission)
                    counts['teams'] += bool(created)
                    task = Task.objects.get(pk=task_id)
                    approach, created = self._create_approach(team, task, submission)
                    counts['approaches'] += bool(created)
                    s = Submission(
                        created=submission['created'],
                        creator=u,
                        approach=approach,
                        accepted_terms=False,
                        status='succeeded',
                        overall_score=submission['overallScore'],
                        score=self.get_score(submission['_id'])['score'],
                    )
                    s.save()
                    s = self._add_submission_file(s, submission)
                    s.save()
                    counts['submissions'] += 1

            print(task_id, json.dumps(counts, indent=4))
