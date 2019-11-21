import logging
import os

import django_heroku
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


from .base import *  # noqa: F401, F403


ALLOWED_HOSTS = ['challenge.isic-archive.com']
SECRET_KEY = os.environ['SECRET_KEY']
CORS_ORIGIN_ALLOW_ALL = True  # todo change

sentry_sdk.init(
    dsn=os.environ['SENTRY_DSN'],
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
        LoggingIntegration(level=logging.INFO, event_level=logging.WARNING),
    ],
    send_default_pii=True,
)

CELERY_BROKER_POOL_LIMIT = 1
CELERY_TASK_ACKS_LATE = True
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
DEFAULT_FILE_STORAGE = 'core.storage_backends.TimeoutS3Boto3Storage'
AWS_S3_MAX_MEMORY_SIZE = 5 * 1024 * 1024
AWS_STORAGE_BUCKET_NAME = 'isic-challenge-stade'
AWS_S3_FILE_OVERWRITE = False
AWS_AUTO_CREATE_BUCKET = False
AWS_QUERYSTRING_EXPIRE = 3600 * 6  # 6 hours
AWS_DEFAULT_ACL = None

INSTALLED_APPS.append('joist')  # noqa: F405
JOIST_UPLOAD_STS_ARN = os.environ['UPLOAD_STS_ARN']

EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'noreply@isic-archive.com'
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 10

MAILCHIMP_API_KEY = os.environ['MAILCHIMP_API_KEY']
MAILCHIMP_API_URL = 'https://us17.api.mailchimp.com/'
MAILCHIMP_LIST_ID = 'aa0e7aa1b1'

ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

django_heroku.settings(locals())
