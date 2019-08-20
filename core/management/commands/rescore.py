import csv
import math
import sys
from typing import Iterable

from dictdiffer import diff
from django.core.management.base import BaseCommand

import core.models
from core.models import Submission, Task
from core.tasks import _score_submission, score_submission


def changes(s1: Submission, s2: Submission) -> dict:
    c = {}

    if s1.status != s2.status:
        c['status'] = [s1.status, s2.status]

    if s1.overall_score != s2.overall_score:
        if (s1.overall_score is None or s2.overall_score is None) or (
            not math.isclose(s1.overall_score, s2.overall_score)
        ):
            c['overall score'] = [s1.overall_score, s2.overall_score]

    if s1.validation_score != s2.validation_score:
        if (s1.validation_score is None or s2.validation_score is None) or (
            not math.isclose(s1.validation_score, s2.validation_score)
        ):
            c['validation score'] = [s1.validation_score, s2.validation_score]

    for d in diff(s1.score, s2.score):
        if d[0] == 'change':
            key = d[1] if d[1] != '' else 'score'

            if key in ['roc', 'score']:
                c[key] = ['', 'changed']
            else:
                c[key] = d[2]
        elif d[0] == 'remove':
            c[d[1]] = ['', 'removed']
        else:
            raise Exception(d)

    return c


class Command(BaseCommand):
    help = 'Rescore submissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            choices=core.models.SUBMISSION_STATUS_CHOICES.keys(),
            help='The status of submission to rescore.',
        )

        parser.add_argument(
            '--dry-run', action='store_true', help='Just print the difference in rescoring'
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
