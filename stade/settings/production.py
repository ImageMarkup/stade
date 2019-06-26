import os

import django_heroku
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

from .base import *

SECRET_KEY = os.environ["SECRET_KEY"]
CORS_ORIGIN_ALLOW_ALL = True  # todo change

sentry_sdk.init(
    dsn="https://f3276f78f8aa48739e911d6e8e8a7aed@sentry.io/1435057",
    integrations=[DjangoIntegration(), CeleryIntegration()],
)

CELERY_BROKER_POOL_LIMIT = 1
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_STORAGE_BUCKET_NAME = "isic-challenge-stade"
AWS_S3_FILE_OVERWRITE = False
AWS_AUTO_CREATE_BUCKET = False
AWS_DEFAULT_ACL = None
EMAIL_HOST = "smtp.mailgun.org"
EMAIL_PORT = 587
EMAIL_HOST_USER = "noreply@isic-archive.com"
EMAIL_HOST_PASSWORD = "87c18a4bca555dd42828c98f0451185c-6140bac2-7248eaa1"
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 10

MAILCHIMP_API_KEY = os.environ['MAILCHIMP_API_KEY']
MAILCHIMP_API_URL = 'https://us17.api.mailchimp.com/'
MAILCHIMP_LIST_ID = 'aa0e7aa1b1'

django_heroku.settings(locals())
