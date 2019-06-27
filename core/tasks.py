import json

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings

from core.models import Submission, Task
from django.core.mail import send_mail
from isic_challenge_scoring.types import ScoreException
from isic_challenge_scoring.task3 import compute_metrics


logger = get_task_logger(__name__)


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
        with submission.approach.task.test_ground_truth_file.open() as truth_file, submission.test_prediction_file.open() as prediction_file:
            results = compute_metrics(truth_file, prediction_file)
        submission.score = results
        submission.overall_score = results['overall']
        submission.status = "succeeded"
        submission.save()
        submission.score_history.create(
            score=submission.score, overall_score=submission.overall_score
        )
        if notify:
            send_mail(
                f"{settings.EMAIL_SUBJECT_PREFIX}Submission succeeded",
                f"It did!{json.dumps(results)}",
                settings.DEFAULT_FROM_EMAIL,
                [submission.creator.email],
            )
    except ScoreException as e:
        submission.status = "failed"
        submission.fail_reason = e.args[0]
        submission.save()
        if notify:
            send_mail(
                f"{settings.EMAIL_SUBJECT_PREFIX}Submission failed",
                f"it dun work, {e.args[0]}",
                settings.DEFAULT_FROM_EMAIL,
                [submission.creator.email],
            )
    except Exception:
        logger.exception(f"internal error scoring submission {submission.id}")
        submission.status = "internal_failure"
        submission.save()
        if notify:
            send_mail(
                f"{settings.EMAIL_SUBJECT_PREFIX}Submission failed (internal error)",
                f"It failed due to internal error, it will be rescored when fixed, or an administrator will contact you.",
                settings.DEFAULT_FROM_EMAIL,
                [submission.creator.email],
            )
