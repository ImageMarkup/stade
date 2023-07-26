from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
import requests

logger = get_task_logger(__name__)


@shared_task(soft_time_limit=10, time_limit=15)
def add_mailchimp_subscriber(email):
    resp = requests.post(
        f'{settings.STADE_MAILCHIMP_API_URL}/3.0/lists/{settings.STADE_MAILCHIMP_LIST_ID}/members',
        auth=('', settings.STADE_MAILCHIMP_API_KEY),
        headers={'Content-Type': 'application/json'},
        json={'email_address': email, 'status': 'subscribed', 'tags': ['stade']},
    )
    resp_json = resp.json()

    # MailChimp API doesn't return special status codes for members already existing, or fake
    # emails So ignore them (since there's nothing we can really do) and only raise in the case of
    # a different, more legitimate error.
    if (
        not resp.ok
        and resp_json['title'] != 'Member Exists'
        and 'looks fake or invalid' not in resp_json['detail']
        and 'signed up to a lot of lists very recently' not in resp_json['detail']
    ):
        logger.info(resp.text)
        resp.raise_for_status()
