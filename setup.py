from setuptools import setup

setup(
    name='stade',
    version='0.1',
    python_requires='>=3.7.0',
    install_requires=[
        'boto3',
        'celery',
        'dictdiffer',
        'django<3',
        'django-admin-display',
        'django-allauth',
        'django-cors-headers',
        'django-import-export',
        'djangorestframework',
        'django-markdownify',
        'django-storages',
        'isic-challenge-scoring',
        'psycopg2',
        'requests',
        'rules',
        'uritemplate',
        # Production-only
        'django-heroku',
        'gunicorn',
        'sentry_sdk',
        # Development-only
        'django-debug-toolbar',
        'django-extensions',
        # TODO: 'psycopg2-binary' instead of 'psycopg2' for development
    ],
)
