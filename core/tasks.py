from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import render_to_string

from isic_challenge_scoring.task3 import compute_metrics
from isic_challenge_scoring.types import ScoreException

from core.models import Submission, Task, TeamInvitation

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
