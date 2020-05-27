from setuptools import setup

setup(
    name='stade',
    version='0.1',
    python_requires='>=3.7.0',
    install_requires=[
        'boto3',
        'cachier',
        'celery',
        'dictdiffer',
        'django',
        'django-admin-display',
        'django-allauth',
        'django-cors-headers',
        'django-import-export',
        'django-markdownify',
        'django-s3-file-field',
        'django-storages',
        'djangorestframework',
        'isic-challenge-scoring',
        'psycopg2',
        'python-magic',
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
        'django-minio-storage',
        # TODO: 'psycopg2-binary' instead of 'psycopg2' for development
    ],
)
