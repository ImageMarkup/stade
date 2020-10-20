release: ./manage.py migrate
web: gunicorn --bind 0.0.0.0:$PORT --preload --max-requests 100 stade.wsgi
worker: celery worker --app stade.celery --loglevel info --without-heartbeat
