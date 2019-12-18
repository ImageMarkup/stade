import os
from typing import List

from .base import *  # noqa: F401, F403

CORS_ORIGIN_ALLOW_ALL = True
SECRET_KEY = 'insecuresecret'
DEBUG = True
ALLOWED_HOSTS: List[str] = []
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'stade',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': os.environ.get('POSTGRES_HOST', '127.0.0.1'),
        'PORT': '5432',
    }
}
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
MEDIA_ROOT = '/uploads/'
MEDIA_URL = '/uploads/'
INSTALLED_APPS += ['debug_toolbar', 'django_extensions']  # noqa: F405

MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405

INTERNAL_IPS = ['127.0.0.1', '0.0.0.0']


def show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': show_toolbar}

# Celery
CELERY_BROKER_URL = 'amqp://localhost:5672/'
