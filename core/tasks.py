import csv
import os
import tempfile
import time
from zipfile import ZipFile

import boto3
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db import connection, transaction
from django.db.models import Count, Q
from django.template.loader import render_to_string

from isic_challenge_scoring.task3 import compute_metrics
from isic_challenge_scoring.types import ScoreException

from core.models import Approach, Submission, Task, TeamInvitation

logger = get_task_logger(__name__)


def notify_creator_of_scoring_attempt(submission):
    context = {'submission': submission, 'url': f'https://{Site.objects.get_current().domain}'}
    message = render_to_string(f'email/submission_{submission.status}.txt', context)
    html_message = render_to_string(f'email/submission_{submission.status}.html', context)
    subject_prefix = f'[{submission.approach.task.name}] '

    if submission.status == 'succeeded':
        subject = f'{subject_prefix}Submission succeeded (#{submission.id})'
    elif submission.status == 'failed':
        subject = f'{subject_prefix}Submission failed (#{submission.id})'
    elif submission.status == 'internal_failure':
        subject = f'{subject_prefix}Submission failed (internal error) (#{submission.id})'
    else:
        raise Exception(f'Encountered unexpected submission status {submission.status}.')

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [submission.creator.email],
        html_message=html_message,
    )


def upload_and_sign_submission_bundle(bundle_filename):
    s3 = boto3.client('s3')
    key = f'submission-bundles/{bundle_filename}'

    with open(bundle_filename, 'rb') as data:
        s3.upload_fileobj(data, settings.AWS_STORAGE_BUCKET_NAME, key)

    return s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key},
        ExpiresIn=86400,
    )


def generate_bundle_as_zip(task, successful_approaches):
    current_time = int(round(time.time() * 1000))
    file_prefix = f'task-{task.id}-{current_time}'
    bundle_filename = f'{file_prefix}-submissions.zip'
    with ZipFile(bundle_filename, 'w') as bundle:
        # add the test ground truth file
        with task.test_ground_truth_file.open() as f:
            bundle.writestr(f'{file_prefix}/test_ground_truth.csv', f.read())

        # add the submitter metadata file
        with tempfile.NamedTemporaryFile('w') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(
                ['approach_id', 'approach_name', 'team_id', 'team_name', 'overall_score']
            )

            for approach in successful_approaches:
                writer.writerow(
                    [
                        approach.id,
                        approach.name,
                        approach.team.id,
                        approach.team.name,
                        approach.latest_successful_submission.overall_score,
                    ]
                )

            outfile.flush()

            bundle.write(outfile.name, f'{file_prefix}/submitter_metadata.csv')

        for approach in successful_approaches:
            with approach.manuscript.open() as f:
                bundle.writestr(f'{file_prefix}/{approach.id}/manuscript.pdf', f.read())

            with approach.latest_successful_submission.test_prediction_file.open() as f:
                bundle.writestr(f'{file_prefix}/{approach.id}/predictions.csv', f.read())

    return bundle_filename


@shared_task
def generate_submission_bundle(task_id, notify_user_id):
    with transaction.atomic():
        cursor = connection.cursor()
        cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')

        task = Task.objects.get(pk=task_id)
        user = User.objects.only('email').get(pk=notify_user_id)
        successful_approaches = (
            Approach.objects.annotate(
                num_successful_submissions=Count(
                    'submission', filter=Q(submission__status='succeeded')
                )
            )
            .filter(task=task, num_successful_submissions__gt=0)
            .select_related('team')
        )

        bundle_filename = generate_bundle_as_zip(task, successful_approaches)

    signed_url = upload_and_sign_submission_bundle(bundle_filename)

    message = render_to_string(
        f'email/submission_bundle_generated.txt', {'submission_bundle_url': signed_url}
    )
    send_mail('Submission bundle generated', message, settings.DEFAULT_FROM_EMAIL, [user.email])

    os.remove(bundle_filename)


@shared_task
def rescore_task_submissions(task_id):
    task = Task.objects.get(pk=task_id)

    for submission in Submission.objects.filter(approach__task=task).all():
        score_submission.delay(submission.id, False)


@shared_task
def score_submission(submission_id, notify=True):
    submission = Submission.objects.get(pk=submission_id)
    submission.status = 'scoring'
    submission.save()

    try:
        with submission.approach.task.test_ground_truth_file.open() as truth_file:
            with submission.test_prediction_file.open() as prediction_file:
                results = compute_metrics(truth_file, prediction_file)
        submission.score = results
        submission.overall_score = results['overall']
        submission.validation_score = results['validation']
        submission.status = 'succeeded'
        submission.save()
        submission.score_history.create(
            score=submission.score, overall_score=submission.overall_score
        )
    except ScoreException as e:
        submission.status = 'failed'
        submission.fail_reason = e.args[0]
        submission.save()
    except Exception:
        logger.exception(f'internal error scoring submission {submission.id}')
        submission.status = 'internal_failure'
        submission.save()
    finally:
        if notify and submission.status != 'scoring':
            notify_creator_of_scoring_attempt(submission)


@shared_task
def send_team_invitation(invite_id):
    invite = TeamInvitation.objects.get(pk=invite_id)
    existing_user = User.objects.filter(email=invite.recipient).exists()
    context = {
        'invite': invite,
        'sent_from': ' '.join([invite.sender.first_name, invite.sender.last_name]),
        'url': f'https://{Site.objects.get_current().domain}',
    }

    if existing_user:
        send_mail(
            f"[{invite.team.challenge}] You've been invited to join {invite.team.name}!",
            render_to_string('email/team_invite_existing_user.txt', context),
            settings.DEFAULT_FROM_EMAIL,
            [invite.recipient],
            html_message=render_to_string(f'email/team_invite_existing_user.html', context),
        )
    else:
        send_mail(
            "You've been invited to join the ISIC Challenge!",
            render_to_string('email/team_invite_new_user.txt', context),
            settings.DEFAULT_FROM_EMAIL,
            [invite.recipient],
            html_message=render_to_string(f'email/team_invite_new_user.html', context),
        )
