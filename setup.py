from setuptools import setup

setup(
    name='stade',
    version='0.1',
    python_requires='>=3.7.0',
    setup_requires=[
        'boto3',
        'django',
        'django-cors-headers',
        'djangorestframework',
        'django-storages',
        'celery',
        'isic-challenge-scoring',
        'requests',
    ],
)
