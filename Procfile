release: ./manage.py migrate
web: gunicorn --bind 0.0.0.0:$PORT stade.wsgi
worker: REMAP_SIGTERM=SIGQUIT celery --app stade.celery worker --loglevel INFO --without-heartbeat
