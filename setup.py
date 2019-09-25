from setuptools import setup

setup(
    name='stade',
    version='0.1',
    python_requires='>=3.7.0',
    install_requires=[
        'boto3',
        'coreapi',  # todo why does this have to be pulled in as a top level?
        'django',
        'django-allauth',
        'django-cors-headers',
        'django-import-export',
        'djangorestframework',
        'django-markdownify',
        'django-storages',
        'celery',
        'isic-challenge-scoring==4.3.2',
        'psycopg2',
        'requests',
        'rules',
    ],
)
