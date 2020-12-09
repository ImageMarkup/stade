from pathlib import Path

from setuptools import find_packages, setup

readme_file = Path(__file__).parent / 'README.md'
if readme_file.exists():
    with readme_file.open() as f:
        long_description = f.read()
else:
    # WHen this is first installed in development Docker, README.md is not available
    long_description = ''

setup(
    name='stade',
    version='0.1.0',
    description='',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache 2.0',
    author='Kitware, Inc',
    author_email='kitware@kitware.com',
    keywords='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django :: 3.0',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python',
    ],
    python_requires='>=3.8',
    packages=find_packages(),
    install_requires=[
        # 'boto3',
        'dictdiffer',
        'django-allauth',
        'django-import-export',
        'django-markdownify',
        'isic-challenge-scoring',
        'requests',
        'rules',
        'uritemplate',
        'django-girder-utils',
        'celery',
        'django',
        'django-admin-display',
        'django-composed-configuration',
        'django-configurations[database,email]',
        'django-cors-headers',
        'django-extensions',
        'django-filter',
        'django-s3-file-field',
        'djangorestframework',
        'drf-extensions',
        'drf-yasg2',
        'psycopg2',
        'rich',
        'whitenoise[brotli]',
        # Production-only
        'django-storages[boto3]',
        'gunicorn',
        'sentry-sdk',
        # Development-only
        'django-debug-toolbar',
        'django-minio-storage>=0.3.10',
    ],
    extras_require={'dev': ['ipython', 'tox']},
)
