from datetime import datetime
import json
import re

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
import requests
import warnings

from core.models import Approach, Challenge, Submission, Task, Team


class Command(BaseCommand):
    help = 'Migrate 2018 Live Covalic data into Stade'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)
        parser.add_argument('girder_token', type=str)

    def handle(self, *args, **options):
        warnings.simplefilter("ignore")
        with open(options['json_file'], 'rb') as data_file:
            file_content = json.load(data_file)
            data = json.loads(file_content)
            users = data['users']
            challenge = data['challenges']
            tasks = data['tasks']
            teams = data['teams']
            approaches = data['approaches']
            submissions = data['submissions']

            # for user in users:
            #     if not User.objects.filter(email=user['email']).exists():
            #         user_obj = User.objects.create(
            #             username=user['email'][:150],
            #             password='dummy',
            #             email=user['email'],
            #             first_name=user['first_name'][:30],
            #             last_name=user['last_name'][:150],
            #             is_active=True,
            #             date_joined=datetime.utcfromtimestamp(user['created']['$date'] / 1000),
            #         )
            #         user_obj.set_unusable_password()
            #         user_obj.save()
            # print('users done')

            # challenge_id = Challenge.objects.create(
            #     created=datetime.utcfromtimestamp(challenge['created']['$date'] / 1000),
            #     name=challenge['name'],
            #     locked=challenge['locked'],
            #     position=challenge['position'],
            # ).id
            # print('challenges done')

            # for task in tasks:
            #     Task.objects.create(
            #         created=datetime.utcfromtimestamp(task['created']['$date'] / 1000),
            #         challenge_id=challenge_id,
            #         name=task['name'],
            #         description=task['description'] if task['description'] is not None else '',
            #         short_description=task['short_description']
            #         if task['short_description'] is not None
            #         else '',
            #         locked=task['locked'],
            #         hidden=task['hidden'],
            #         scores_published=task['scores_published'],
            #         test_ground_truth_file=task['test_ground_truth_file'],
            #     )
            # print('tasks done')

            # for team in teams:
            #     team_obj = Team.objects.create(
            #         created=datetime.utcfromtimestamp(team['created']['$date'] / 1000),
            #         creator=User.objects.get(email=team['creator']['email']),
            #         name=team['name'],
            #         institution=team['institution'],
            #         institution_url=team['institution_url'],
            #         challenge_id=challenge_id,
            #     )
            #     for user in team['users']:
            #         team_obj.users.add(User.objects.get(email=user['email']))
            #     team_obj.save()
            # print('teams done')

            # for approach in approaches:
            #     if approach['manuscript'] is None:
            #         file = None
            #         name = None
            #     else:
            #         content, name = download_file(approach['manuscript'], options['girder_token'])
            #         file = SimpleUploadedFile(name, content)
            #     Approach.objects.create(
            #         created=datetime.utcfromtimestamp(approach['created']['$date'] / 1000),
            #         name=approach['name'][:100],
            #         uses_external_data=approach['uses_external_data']
            #         if approach['uses_external_data'] is not None
            #         else False,  # default to False if None
            #         manuscript=file,
            #         manuscript_name=name,
            #         task_id=Task.objects.get(
            #             name__exact=approach['task']['name'],
            #             created=datetime.utcfromtimestamp(
            #                 approach['task']['created']['$date'] / 1000
            #             ),
            #             challenge_id=challenge_id,
            #         ).id,
            #         team_id=Team.objects.get(
            #             name__exact=approach['team']['name'], challenge_id=challenge_id
            #         ).id,
            #     )
            # print('approaches done')

            count = 0
            for submission in submissions:
                count += 1
                exists = Submission.objects.filter(
                    created=datetime.utcfromtimestamp(submission['created']['$date'] / 1000),
                    creator=User.objects.get(email=submission['creator']['email']),
                ).exists()
                if not exists:
                    if submission['test_prediction_file'] is None:
                        file = None
                        name = None
                    else:
                        content, name = download_file(
                            submission['test_prediction_file'], options['girder_token']
                        )
                        file = SimpleUploadedFile(name, content)
                    Submission.objects.create(
                        created=datetime.utcfromtimestamp(submission['created']['$date'] / 1000),
                        creator=User.objects.get(email=submission['creator']['email']),
                        approach_id=Approach.objects.get(
                            name=submission['approach']['name'][:100],
                            created=datetime.utcfromtimestamp(
                                submission['approach']['created']['$date'] / 1000
                            ),
                        ).id,
                        accepted_terms=submission['accepted_terms'],
                        test_prediction_file=file,
                        test_prediction_file_name=submission['test_prediction_file_name'],
                        status=submission['status'],
                        score=submission['score'],
                        overall_score=submission['overall_score'],
                        fail_reason=submission['fail_reason']
                        if submission['fail_reason'] is not None
                        else '',
                    )
                print(count)
            print('submissions done')


def download_file(url, token):
    try:
        print(url)
        if 'submission.challenge.isic-archive.com' in url:
            r = requests.get(url, allow_redirects=True, headers={'girder-token': token})
        else:
            r = requests.get(url, allow_redirects=True)
        r.raise_for_status()

        if 'Content-Disposition' in r.headers.keys():
            fname = re.findall('filename=(.+)', r.headers['Content-Disposition'])[0].strip('"')
        else:
            fname = url.split('/')[-1]
        content = r.content

        return content, fname
    except Exception as e:
        print(e)
        return '', ''
