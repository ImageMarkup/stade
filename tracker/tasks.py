from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
import requests


logger = get_task_logger(__name__)


@shared_task
def add_mailchimp_subscriber(email):
    r = requests.post(
        f'{settings.MAILCHIMP_API_URL}/3.0/lists/{settings.MAILCHIMP_LIST_ID}/members',
        auth=('', settings.MAILCHIMP_API_KEY),
        headers={'Content-Type': 'application/json'},
        json={'email_address': email, 'status': 'subscribed', 'tags': ['stade']},
    )

    if not r.ok and r.json()['title'] != 'Member Exists':
        logger.error(r.text)
        r.raise_for_status()
