from __future__ import annotations

from pathlib import Path

from composed_configuration import (
    ComposedConfiguration,
    ConfigMixin,
    DevelopmentBaseConfiguration,
    HerokuProductionBaseConfiguration,
    ProductionBaseConfiguration,
    TestingBaseConfiguration,
)
from configurations import values


class StadeMixin(ConfigMixin):
    WSGI_APPLICATION = 'stade.wsgi.application'
    ROOT_URLCONF = 'stade.urls'

    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    @staticmethod
    def before_binding(configuration: ComposedConfiguration) -> None:
        # Install local apps first, to ensure any overridden resources are found first
        configuration.INSTALLED_APPS = [
            'stade.core.apps.CoreConfig',
            'stade.tracker.apps.TrackerConfig',
            # jazzmin overrides django.contrib.admin templates
            # jazzmin is broken as of Django 3.2, see https://github.com/farridav/django-jazzmin/issues/281  # noqa
            # 'jazzmin',
        ] + configuration.INSTALLED_APPS

        # Install additional apps
        configuration.INSTALLED_APPS += [
            'import_export',
            'markdownify',
            'rules.apps.AutodiscoverRulesConfig',
            's3_file_field',
        ]

        configuration.AUTHENTICATION_BACKENDS.insert(0, 'rules.permissions.ObjectPermissionBackend')

    JAZZMIN_SETTINGS = {'related_modal_active': True}
    SHELL_PLUS_IMPORTS = ['from stade.core.tasks import *']

    TIME_ZONE = 'America/New_York'

    # Celery
    # TODO: concurrency could be increased for non-memory intensive tasks
    CELERY_WORKER_CONCURRENCY = 1

    MARKDOWNIFY_BLEACH = False

    STADE_MAILCHIMP_API_URL = 'https://us17.api.mailchimp.com/'
    STADE_MAILCHIMP_API_KEY = values.SecretValue()
    STADE_MAILCHIMP_LIST_ID = 'aa0e7aa1b1'

    # TODO: is this needed?
    ACCOUNT_FORMS = {
        'signup': 'stade.core.forms.CustomSignupForm',
        'reset_password_from_key': 'stade.core.forms.CustomResetPasswordKeyForm',
    }

    # Workaround for static file storage to work correctly on Django 4.
    # Taken from https://github.com/axnsan12/drf-yasg/issues/761#issuecomment-1031381674
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'


class DevelopmentConfiguration(StadeMixin, DevelopmentBaseConfiguration):
    # Not required
    STADE_MAILCHIMP_API_KEY = values.Value()
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }


class TestingConfiguration(StadeMixin, TestingBaseConfiguration):
    STADE_MAILCHIMP_API_KEY = None


class ProductionConfiguration(StadeMixin, ProductionBaseConfiguration):
    DEFAULT_FILE_STORAGE = 'stade.core.storage_backends.TimeoutS3Boto3Storage'
    # TODO: What about this?
    EMAIL_TIMEOUT = 10


class HerokuProductionConfiguration(StadeMixin, HerokuProductionBaseConfiguration):
    DEFAULT_FILE_STORAGE = 'stade.core.storage_backends.TimeoutS3Boto3Storage'
    # TODO: What about this?
    EMAIL_TIMEOUT = 10
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'cache',
        }
    }
