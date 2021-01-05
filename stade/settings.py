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


class StadeConfig(ConfigMixin):
    WSGI_APPLICATION = 'stade.wsgi.application'
    ROOT_URLCONF = 'stade.urls'

    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    @staticmethod
    def before_binding(configuration: ComposedConfiguration) -> None:
        # Insert before other apps with allauth templates
        # TODO: remove
        auth_app_index = configuration.INSTALLED_APPS.index(
            'composed_configuration.authentication.apps.AuthenticationConfig'
        )
        admin_index = configuration.INSTALLED_APPS.index('django.contrib.admin')
        configuration.INSTALLED_APPS.insert(admin_index, 'jazzmin')
        configuration.INSTALLED_APPS.insert(auth_app_index, 'stade.core.apps.CoreConfig')

        configuration.INSTALLED_APPS += [
            'django.contrib.humanize',
            'import_export',
            'markdownify',
            'rules.apps.AutodiscoverRulesConfig',
            's3_file_field',
            'stade.tracker.apps.TrackerConfig',
        ]

        configuration.AUTHENTICATION_BACKENDS.insert(0, 'rules.permissions.ObjectPermissionBackend')

    JAZZMIN_SETTINGS = {'related_modal_active': True}
    SHELL_PLUS_IMPORTS = ['from stade.core.tasks import *']

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


class DevelopmentConfiguration(StadeConfig, DevelopmentBaseConfiguration):
    # Not required
    STADE_MAILCHIMP_API_KEY = values.Value()


class TestingConfiguration(StadeConfig, TestingBaseConfiguration):
    STADE_MAILCHIMP_API_KEY = None


class ProductionConfiguration(StadeConfig, ProductionBaseConfiguration):
    DEFAULT_FILE_STORAGE = 'stade.core.storage_backends.TimeoutS3Boto3Storage'
    # TODO: What about this?
    EMAIL_TIMEOUT = 10


class HerokuProductionConfiguration(StadeConfig, HerokuProductionBaseConfiguration):
    DEFAULT_FILE_STORAGE = 'stade.core.storage_backends.TimeoutS3Boto3Storage'
    # TODO: What about this?
    EMAIL_TIMEOUT = 10
