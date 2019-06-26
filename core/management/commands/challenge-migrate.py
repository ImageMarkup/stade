from django.core.files import File
from django.contrib.auth.models import User

from core.models import Challenge, Task, Team, Approach, Submission, Score
from django.core.management.base import BaseCommand

import json
from datetime import datetime
import pprint
import requests
import re
import io
from django.core.files.uploadedfile import SimpleUploadedFile


class Command(BaseCommand):
    help = "Migrate Covalic data into Stade"

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)
        parser.add_argument('girder_token', type=str)

    def handle(self, *args, **options):
        with open(options['json_file'], "rb") as data_file:
            file_content = json.load(data_file)
            data = json.loads(file_content)
            users = data['users']
            challenges = data['challenges']
            tasks = data['tasks']
            teams = data['teams']
            approaches = data['approaches']
            submissions = data['submissions']
            scores = data['scores']

            user_objs = []
            for user in users:
                user_obj = User.objects.create(
                    username=user['email'][:150],
                    password='dummy',
                    email=user['email'],
                    first_name=user['first_name'][:30],
                    last_name=user['last_name'][:150],
                    is_active=False,
                    date_joined=datetime.utcfromtimestamp(user['created']['$date'] / 1000),
                )
                user_obj.set_unusable_password()
                user_obj.save()
                user_objs.append(user_obj)
            print('users done')

            challenge_objs = []
            for challenge in challenges:
                challenge_objs.append(
                    Challenge.objects.create(
                        created=challenge['created'],
                        name=challenge['name'],
                        position=challenge['position'],
                        active=False,
                    )
                )
            print('challenges done')

            task_objs = []
            for task in tasks:
                task_objs.append(
                    Task.objects.create(
                        created=task['created'],
                        challenge_id=challenge_objs[challenges.index(task['challenge'])].id,
                        name=task['name'][:100],
                        test_ground_truth_file=task['data_file'],
                        active=False,
                        visible=True,
                        description='',
                    )
                )
            print('tasks done')

            team_objs = []
            for team in teams:
                team_obj = Team.objects.create(
                    created=team['created'],
                    creator=user_objs[users.index(team['creator'])],
                    name=team['name'][:100],
                    institution=team['institution'] if team['institution'] is not None else '',
                    institution_url=team['institution_url']
                    if team['institution_url'] is not None
                    else '',
                    challenge_id=challenge_objs[challenges.index(team['challenge'])].id,
                )
                team_obj.save()
                for u in team['users']:
                    team_obj.users.add(user_objs[users.index(u)])
                team_objs.append(team_obj)
            print('teams done')

            approach_objs = []
            for approach in approaches:
                try:
                    if approach['manuscript'] is None:
                        file = None
                        name = None
                    else:
                        content, name = download_file(
                            approach['manuscript'], options['girder_token']
                        )
                        file = SimpleUploadedFile(name, content)

                    approach_objs.append(
                        Approach.objects.create(
                            created=approach['created'],
                            name=approach['name'][:100],
                            uses_external_data=approach['uses_external_data']
                            if approach['uses_external_data'] is not None
                            else False,  # default to False if None
                            manuscript=file,
                            manuscript_name=name,
                            task_id=task_objs[tasks.index(approach['task'])].id,
                            team_id=team_objs[teams.index(approach['team'])].id,
                        )
                    )
                except Exception as e:
                    pprint.pprint(approach)
                    raise e
            print('approaches done')

            submission_objs = []
            for submission in submissions:
                if submission['test_prediction_file'] is None:
                    file = None
                    name = None
                else:
                    content, name = download_file(
                        submission['test_prediction_file'], options['girder_token']
                    )
                    file = SimpleUploadedFile(name, content)
                submission_objs.append(
                    Submission.objects.create(
                        created=submission['created'],
                        creator_id=user_objs[users.index(submission['user'])].id,
                        approach_id=approach_objs[approaches.index(submission['approach'])].id,
                        test_prediction_file=file,
                        test_prediction_file_name=name,
                        status=submission['status'],
                        accepted_terms=True,
                    )
                )
            print('submissions done')

            score_objs = []
            for score in scores:
                score_objs.append(
                    Score.objects.create(
                        submission_id=submission_objs[submissions.index(score['submission'])].id,
                        created=score['created'],
                        score=score['score'],
                        fail_reason=score['fail_reason']
                        if score['fail_reason'] is not None
                        else '',
                        overall_score=score['overall_score'],
                    )
                )
            print('scores done')


def download_file(url, token):
    try:
        print(url)
        if 'challenge.kitware.com' in url:
            r = requests.get(url, allow_redirects=True, headers={'girder-token': token})
        else:
            r = requests.get(url, allow_redirects=True)

        if "Content-Disposition" in r.headers.keys():
            fname = re.findall("filename=(.+)", r.headers["Content-Disposition"])[0].strip('"')
        else:
            fname = url.split("/")[-1]
        content = r.content

        return content, fname
    except Exception as e:
        print(e)
        return '', ''
