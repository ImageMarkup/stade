import csv
import sys

from django.core.management.base import BaseCommand

from core.models import Submission
from core.tasks import _score_submission, score_submission
from core.utils import changes


class Command(BaseCommand):
    help = 'Rescore a single submission'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=True,
            help='Just print the difference in rescoring',
        )

        parser.add_argument('submission', help='The submission ID to scope rescoring to.')

    def handle(self, *args, **options):
        try:
            submission = Submission.objects.get(pk=options['submission'])
        except Submission.DoesNotExist:
            self.stderr.write(f'unable to find submission {options["submission"]}')
            sys.exit(1)

        if options['dry_run']:
            new_submission = _score_submission(submission)

            if new_submission.status == 'failed':
                self.stderr.write(f'failed to score submission: {new_submission.fail_reason}')
                return
            elif new_submission.status == 'internal_failure':
                self.stderr.write(f'failed to score submission: internal failure')
                return

            old_submission = Submission.objects.get(pk=submission.id)
            c = changes(old_submission, new_submission)

            writer = csv.DictWriter(sys.stdout, fieldnames=['field', 'before', 'after'])
            writer.writeheader()

            if c:
                for k, v in c.items():
                    writer.writerow({'field': k, 'before': v[0], 'after': v[1]})
        else:
            score_submission.delay(submission.id, notify=False)
