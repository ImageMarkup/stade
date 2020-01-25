import csv
import sys

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from core.models import Submission, Task
from core.tasks import _score_submission, score_submission
from core.utils import changes


class Command(BaseCommand):
    help = 'Rescore task submissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--persist',
            action='store_true',
            default=False,
            help='Persist the scoring changes to the database.',
        )
        parser.add_argument(
            '--status',
            choices=Submission.Status.values,
            help='Only run on submissions with a certain status.',
        )

        parser.add_argument('task', help='The task ID to scope rescoring to.')

    def handle(self, *args, **options):
        try:
            task = Task.objects.get(pk=options['task'])
        except Task.DoesNotExist:
            self.stderr.write(f'unable to find task {options["task"]}')
            sys.exit(1)

        submissions: QuerySet = Submission.objects.filter(approach__task=task).order_by('created')
        if options.get('status'):
            submissions = submissions.filter(status=options['status'])
        self.stderr.write(f'found {submissions.count()} submissions to rescore')

        if options['persist']:
            for submission in submissions:
                score_submission.delay(submission.id, notify=False)
        else:
            writer = csv.DictWriter(
                sys.stdout, fieldnames=['submission', 'field', 'before', 'after']
            )
            writer.writeheader()
            for submission in submissions:
                new_submission = _score_submission(submission)
                old_submission = Submission.objects.get(pk=submission.id)
                c = changes(old_submission, new_submission)

                if c:
                    for k, v in c.items():
                        writer.writerow(
                            {'submission': submission.id, 'field': k, 'before': v[0], 'after': v[1]}
                        )
