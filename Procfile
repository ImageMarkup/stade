release: python manage.py migrate
web: gunicorn --bind 0.0.0.0:$PORT --max-requests 100 stade.wsgi
worker: celery worker --app stade.celery --concurrency 3 --loglevel info --without-gossip --without-mingle --without-heartbeat
