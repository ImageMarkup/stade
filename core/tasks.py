import csv
from datetime import datetime
import io
import os
import tempfile
import uuid
from zipfile import ZipFile

import boto3
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.files import File
from django.core.mail import send_mail
from django.db import connection, transaction
from django.db.models.fields.files import FieldFile
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
    key = f'submission-bundles/{uuid.uuid4()}/{bundle_filename}'

    with open(bundle_filename, 'rb') as data:
        s3.upload_fileobj(data, settings.AWS_STORAGE_BUCKET_NAME, key)

    return s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key},
        ExpiresIn=86400,
    )


def generate_bundle_as_zip(task, successful_approaches):
    current_time = datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')
    bundle_root_dir = f'ISIC-task-{task.id}-submissions-{current_time}'
    bundle_filename = f'{bundle_root_dir}.zip'
    with ZipFile(bundle_filename, 'w') as bundle:
        # add the test ground truth file
        with task.test_ground_truth_file.open() as f:
            bundle.writestr(
                f'{bundle_root_dir}/{os.path.basename(task.test_ground_truth_file.name)}', f.read()
            )

        # add the submitter metadata file
        with tempfile.NamedTemporaryFile('w') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(
                [
                    'approach_id',
                    'approach_name',
                    'uses_external_data',
                    'team_id',
                    'team_name',
                    'overall_score',
                ]
            )

            for approach in successful_approaches:
                writer.writerow(
                    [
                        approach.id,
                        approach.name,
                        approach.uses_external_data,
                        approach.team.id,
                        approach.team.name,
                        approach.latest_successful_submission.overall_score,
                    ]
                )

            outfile.flush()

            bundle.write(outfile.name, f'{bundle_root_dir}/submitter_metadata.csv')

        # add manuscripts and predictions
        prediction_filename = f'predictions.{"zip" if task.type == "segmentation" else "csv"}'
        for approach in successful_approaches:
            if approach.manuscript:  # manuscripts weren't always required in the past (or for live)
                # Even for S3Boto3StorageFile, calling FieldFile.file gives a local File object
                manuscript_file: File = approach.manuscript.file
                bundle.write(
                    manuscript_file.name, f'{bundle_root_dir}/{approach.id}/manuscript.pdf'
                )

            prediction_file: File = approach.latest_successful_submission.test_prediction_file.file
            bundle.write(
                prediction_file.name, f'{bundle_root_dir}/{approach.id}/{prediction_filename}'
            )

    return bundle_filename


@shared_task(time_limit=600)
def generate_submission_bundle(task_id, notify_user_id):
    with transaction.atomic():
        cursor = connection.cursor()
        cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')

        task = Task.objects.get(pk=task_id)
        user = User.objects.only('email').get(pk=notify_user_id)
        successful_approaches = Approach.successful.select_related('team').filter(task=task)

        bundle_filename = generate_bundle_as_zip(task, successful_approaches)

    signed_url = upload_and_sign_submission_bundle(bundle_filename)
    os.remove(bundle_filename)

    message = render_to_string(
        'email/submission_bundle_generated.txt', {'submission_bundle_url': signed_url}
    )
    send_mail('Submission bundle generated', message, settings.DEFAULT_FROM_EMAIL, [user.email])


def _score_submission(submission):
    try:
        truth_file: FieldFile = submission.approach.task.test_ground_truth_file
        prediction_file: FieldFile = submission.test_prediction_file
        # If the S3Boto3Storage backend is used, then the FieldFile contains a S3Boto3StorageFile,
        # which always provides a binary I/O object (requests for a text I/O object are ignored)
        # The FileSystemStorage will honor requests for text I/O mode, but both must be supported
        # consistently
        with truth_file.open('rb'), prediction_file.open('rb'):
            # compute_metrics requires TextIO, so use the wrapper utility
            # Calling .file to get the File object isn't strictly necessary, as the FieldFile will
            # proxy operations to it, but it will make the type checker happy
            results = compute_metrics(
                io.TextIOWrapper(truth_file.file), io.TextIOWrapper(prediction_file.file)
            )
        submission.score = results
        submission.overall_score = results['overall']
        submission.validation_score = results['validation']
        submission.status = 'succeeded'
    except ScoreException as e:
        submission.status = 'failed'
        submission.fail_reason = e.args[0]
        submission.reset_scores()
    except Exception as e:
        logger.exception(f'internal error scoring submission {submission.id}: {e}')
        submission.status = 'internal_failure'
        submission.reset_scores()

    return submission


@shared_task(soft_time_limit=60, time_limit=120)
def score_submission(submission_id, dry_run=False, notify=False):
    submission = Submission.objects.get(pk=submission_id)
    if not dry_run:
        submission.status = 'scoring'
        submission.save()

    submission = _score_submission(submission)

    if not dry_run:
        submission.save()

        if notify:
            notify_creator_of_scoring_attempt(submission)


@shared_task(time_limit=30)
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
