import csv
from datetime import datetime, timedelta
import io
import os
from smtplib import SMTPServerDisconnected
import tempfile
import uuid
from zipfile import ZipFile

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.db import connection, transaction
from django.db.models import Count
from django.db.models.fields.files import FieldFile
from django.template.loader import render_to_string
from girder_utils.files import field_file_to_local_path
from girder_utils.storages import expiring_url
from isic_challenge_scoring import (
    ClassificationScore,
    ScoreException,
    SegmentationScore,
    ValidationMetric,
)

from stade.core.models import Approach, Submission, Task, TeamInvitation

logger = get_task_logger(__name__)


def notify_creator_of_scoring_attempt(submission):
    context = {'submission': submission, 'url': f'https://{Site.objects.get_current().domain}'}
    message = render_to_string(f'email/submission_{submission.status}.txt', context)
    html_message = render_to_string(f'email/submission_{submission.status}.html', context)
    subject_prefix = f'[{submission.approach.task.name}] '

    if submission.status == Submission.Status.SUCCEEDED:
        subject = f'{subject_prefix}Submission succeeded (#{submission.id})'
    elif submission.status == Submission.Status.FAILED:
        subject = f'{subject_prefix}Submission failed (#{submission.id})'
    elif submission.status == Submission.Status.INTERNAL_FAILURE:
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
            writer = csv.DictWriter(
                outfile,
                fieldnames=[
                    'approach_id',
                    'approach_name',
                    'uses_external_data',
                    'team_id',
                    'team_name',
                    'overall_score',
                ],
            )
            writer.writeheader()

            for approach in successful_approaches:
                writer.writerow(
                    {
                        'approach_id': approach.id,
                        'approach_name': approach.name,
                        'uses_external_data': approach.uses_external_data,
                        'team_id': approach.team.id,
                        'team_name': approach.team.name,
                        'overall_score': approach.latest_successful_submission.overall_score,
                    }
                )

            outfile.flush()

            bundle.write(outfile.name, f'{bundle_root_dir}/submitter_metadata.csv')

        # add manuscripts and predictions
        prediction_filename = f'predictions.{"zip" if task.type == "segmentation" else "csv"}'
        for approach in successful_approaches:
            if approach.manuscript:  # manuscripts weren't always required in the past (or for live)
                with field_file_to_local_path(approach.manuscript) as manuscript_path:
                    bundle.write(manuscript_path, f'{bundle_root_dir}/{approach.id}/manuscript.pdf')

            with field_file_to_local_path(
                approach.latest_successful_submission.test_prediction_file
            ) as prediction_path:
                bundle.write(
                    prediction_path, f'{bundle_root_dir}/{approach.id}/{prediction_filename}'
                )

    return bundle_filename


@shared_task(time_limit=60 * 10)
def generate_submission_bundle(task_id, notify_user_id):
    with transaction.atomic():
        cursor = connection.cursor()
        cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')

        task = Task.objects.get(pk=task_id)
        user = User.objects.only('email').get(pk=notify_user_id)
        successful_approaches = Approach.successful.select_related('team').filter(task=task)

        bundle_filename = generate_bundle_as_zip(task, successful_approaches)

    bundle_key = f'submission-bundles/{uuid.uuid4()}/{bundle_filename}'
    with open(bundle_filename, 'rb') as data:
        default_storage.save(bundle_key, data)
    signed_url = expiring_url(default_storage, bundle_key, timedelta(days=1))

    os.remove(bundle_filename)

    message = render_to_string(
        'email/submission_bundle_generated.txt', {'submission_bundle_url': signed_url}
    )
    send_mail('Submission bundle generated', message, settings.DEFAULT_FROM_EMAIL, [user.email])


def _score_submission(submission):
    try:
        truth_file: FieldFile = submission.approach.task.test_ground_truth_file
        prediction_file: FieldFile = submission.test_prediction_file

        if submission.approach.task.type == Task.Type.SEGMENTATION:
            with field_file_to_local_path(truth_file) as truth_file_path, field_file_to_local_path(
                prediction_file
            ) as prediction_file_path:
                score = SegmentationScore.from_zip_file(
                    truth_file_path,
                    prediction_file_path,
                )

        elif submission.approach.task.type == Task.Type.CLASSIFICATION:
            # If the S3Boto3Storage backend is used, then the FieldFile contains a
            # S3Boto3StorageFile, which always provides a binary I/O object (requests for a text
            # I/O object are ignored)
            # The FileSystemStorage will honor requests for text I/O mode, but both must be
            # supported consistently
            with truth_file.open('rb'), prediction_file.open('rb'):
                # compute_metrics requires TextIO, so use the wrapper utility
                # Calling .file to get the File object isn't strictly necessary, as the FieldFile
                # will proxy operations to it, but it will make the type checker happy
                score = ClassificationScore.from_stream(
                    io.TextIOWrapper(truth_file.file),
                    io.TextIOWrapper(prediction_file.file),
                    ValidationMetric(submission.approach.task.metric_field),
                )
        else:
            raise Exception('Unknown task type')

        if submission.approach.task.metric_field == Task.MetricField.AVERAGE_PRECISION:
            submission.overall_score = score.macro_average['ap']
        elif submission.approach.task.metric_field == Task.MetricField.AUC:
            submission.overall_score = score.macro_average['auc']
        elif submission.approach.task.metric_field == Task.MetricField.BALANCED_ACCURACY:
            submission.overall_score = score.aggregate['balanced_accuracy']
        else:
            raise Exception('Unknown task metric field')

        submission.validation_score = score.validation
        submission.score = score.to_dict()
        submission.status = Submission.Status.SUCCEEDED
    except ScoreException as e:
        submission.status = Submission.Status.FAILED
        submission.fail_reason = e.args[0]
        submission.reset_scores()
    except Exception as e:
        logger.exception(f'internal error scoring submission {submission.id}: {e}')
        submission.status = Submission.Status.INTERNAL_FAILURE
        submission.reset_scores()

    return submission


@shared_task(
    soft_time_limit=60 * 20,
    time_limit=60 * 21,
    autoretry_for=(SMTPServerDisconnected,),
    retry_backoff=True,
)
def score_submission(submission_id, dry_run=False, notify=False):
    submission = Submission.objects.get(pk=submission_id)
    if not dry_run:
        submission.status = Submission.Status.SCORING
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
            html_message=render_to_string('email/team_invite_existing_user.html', context),
        )
    else:
        send_mail(
            "You've been invited to join the ISIC Challenge!",
            render_to_string('email/team_invite_new_user.txt', context),
            settings.DEFAULT_FROM_EMAIL,
            [invite.recipient],
            html_message=render_to_string('email/team_invite_new_user.html', context),
        )


@shared_task(
    soft_time_limit=20, time_limit=30, autoretry_for=(SMTPServerDisconnected,), retry_backoff=True
)
def send_possible_abuse_report(user_id):
    user = User.objects.prefetch_related('teams').get(pk=user_id)
    teams = (
        user.teams.select_related('creator')
        .annotate(num_users=Count('users', distinct=True))
        .annotate(num_invites=Count('teaminvitation'))
        .order_by('-created')
    )
    context = {'user': user, 'teams': teams, 'url': f'https://{Site.objects.get_current().domain}'}
    send_mail(
        '[ISIC Challenge] Possible abuse detected',
        render_to_string('email/abuse_report.txt', context),
        settings.DEFAULT_FROM_EMAIL,
        [u.email for u in User.objects.filter(is_superuser=True)],
        html_message=render_to_string('email/abuse_report.html', context),
    )
