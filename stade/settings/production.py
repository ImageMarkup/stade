import os

import django_heroku
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F401, F403

ALLOWED_HOSTS = ['challenge.isic-archive.com']
SECRET_KEY = os.environ['SECRET_KEY']
CORS_ORIGIN_ALLOW_ALL = True  # todo change

sentry_sdk.init(
    dsn=os.environ['SENTRY_DSN'], integrations=[DjangoIntegration(), CeleryIntegration()]
)

CELERY_BROKER_POOL_LIMIT = 1
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'isic-challenge-stade'
AWS_S3_FILE_OVERWRITE = False
AWS_AUTO_CREATE_BUCKET = False
AWS_QUERYSTRING_EXPIRE = 3600 * 6  # 6 hours
AWS_DEFAULT_ACL = None
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
