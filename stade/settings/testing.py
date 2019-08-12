import os
from typing import List

from .base import *  # noqa: F401, F403

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
    },
    'TEST': {'HOST': 'pghost'},
}
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
