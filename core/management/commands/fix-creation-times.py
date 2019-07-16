from datetime import datetime
import json
import warnings
import pprint

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import Approach, Challenge, Submission, Task, Team


class Command(BaseCommand):
    help = 'Migrate 2018 Live Covalic data into Stade'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)

    def handle(self, *args, **options):
        warnings.filterwarnings('ignore')
        with open(options['json_file'], 'rb') as data_file:
            file_content = json.load(data_file)
            data = json.loads(file_content)
            challenges = data['challenges']
            tasks = data['tasks']
            teams = data['teams']
            approaches = data['approaches']
            submissions = data['submissions']

            for challenge in challenges:
                Challenge.objects.filter(name=challenge['name'][:100]).update(
                    created=datetime.utcfromtimestamp(challenge['created']['$date'] / 1000)
                )
            print('challenges done')

            for task in tasks:
                Task.objects.filter(
                    name=task['name'][:100],
                    challenge_id=Challenge.objects.get(name=task['challenge']['name']).id,
                ).update(created=datetime.utcfromtimestamp(task['created']['$date'] / 1000))
            print('tasks done')

            for team in teams:
                Team.objects.filter(
                    name=team['name'][:100],
                    challenge_id=Challenge.objects.get(name=team['challenge']['name']).id,
                ).update(created=datetime.utcfromtimestamp(team['created']['$date'] / 1000))
            print('teams done')

            for approach in approaches:
                Approach.objects.filter(
                    name=approach['name'][:100],
                    task_id=Task.objects.get(
                        name=approach['task']['name'][:100],
                        challenge_id=Challenge.objects.get(
                            name=approach['task']['challenge']['name']
                        ).id,
                    ).id,
                    team_id=Team.objects.get(
                        name=approach['team']['name'][:100],
                        challenge_id=Challenge.objects.get(
                            name=approach['team']['challenge']['name']
                        ).id,
                    ).id,
                ).update(created=datetime.utcfromtimestamp(approach['created']['$date'] / 1000))
            print('approaches done')

            submissions_objs = list(Submission.objects.order_by('created').all())
            for i in range(len(submissions)):
                submission = submissions[i]
                submission_obj = submissions_objs[i]
                if submission['creator']['email'] != submission_obj.creator.email:
                    pprint.pprint(submission)
                    print(submission_obj)
                    raise Exception('Creators dont match')
                if (
                    submission_obj.overall_score < submission['overall_score'] - 0.000000000000001
                    or submission['overall_score'] + 0.000000000000001
                    < submission_obj.overall_score
                ):
                    pprint.pprint(submission)
                    print(submission_obj)
                    raise Exception('Overall scores dont match')
                Submission.objects.filter(id=submission_obj.id).update(
                    created=datetime.utcfromtimestamp(submission['created']['$date'] / 1000)
                )
            print('submissions done')
