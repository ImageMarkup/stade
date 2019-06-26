#!/bin/bash
set -ex

until nc -z db 5432; do sleep 5; done

python /code/manage.py runserver 0.0.0.0:8000
