import csv
import sys
from typing import Iterable

from django.core.management.base import BaseCommand

import core.models
from core.models import Submission, Task
from core.tasks import _score_submission, score_submission
from core.utils import changes


class Command(BaseCommand):
    help = 'Rescore task submissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            choices=core.models.SUBMISSION_STATUS_CHOICES.keys(),
            help='The status of submissions to rescore.',
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=True,
            help='Just print the difference in rescoring',
        )

        parser.add_argument('task', help='The task ID to scope rescoring to.')

    def handle(self, *args, **options):
        try:
            task = Task.objects.get(pk=options['task'])
        except Task.DoesNotExist:
            self.stderr.write(f'unable to find task {options["task"]}')
            sys.exit(1)

        submissions: Iterable[Submission] = Submission.objects.filter(approach__task=task).order_by(
            'created'
        )
        if options.get('status'):
            submissions = submissions.filter(status=options['status'])
        self.stderr.write(f'found {submissions.count()} submissions to rescore')

        if options['dry_run']:
            writer = csv.DictWriter(
                sys.stdout, fieldnames=['submission', 'field', 'before', 'after']
            )
            writer.writeheader()

        for submission in submissions:
            if options['dry_run']:
                new_submission = _score_submission(submission)
                old_submission = Submission.objects.get(pk=submission.id)
                c = changes(old_submission, new_submission)

                if c:
                    for k, v in c.items():
                        writer.writerow(
                            {'submission': submission.id, 'field': k, 'before': v[0], 'after': v[1]}
                        )
            else:
                score_submission.delay(submission.id, notify=False)
