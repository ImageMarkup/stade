from pathlib import Path

from setuptools import find_packages, setup

readme_file = Path(__file__).parent / 'README.md'
if readme_file.exists():
    with readme_file.open() as f:
        long_description = f.read()
else:
    # When this is first installed in development Docker, README.md is not available
    long_description = ''

setup(
    name='stade',
    version='0.1.0',
    description='',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache 2.0',
    author='Kitware, Inc.',
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
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python',
    ],
    python_requires='>=3.12',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'celery',
        'dictdiffer',
        'django>=5,<6.0',
        'django-allauth',
        'django-configurations[database,email]',
        'django-extensions',
        'django-filter',
        'django-girder-utils',
        'django-import-export',
        'django-jazzmin',
        'django-markdownify',
        'django-oauth-toolkit',
        'djangorestframework',
        'drf-yasg',
        'isic-challenge-scoring>=5.6',
        'requests',
        'rules',
        # See https://github.com/axnsan12/drf-yasg/issues/874
        'setuptools',
        'uritemplate',
        # Production-only
        'django-composed-configuration[prod]>=0.20.1',
        'django-s3-file-field[s3]>=1',
        'gunicorn',
    ],
    extras_require={
        'dev': [
            'django-composed-configuration[dev]',
            'django-debug-toolbar',
            'django-s3-file-field[minio]',
            'ipython',
            'tox',
        ]
    },
)
