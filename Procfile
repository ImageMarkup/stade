release: python manage.py migrate
web: gunicorn --bind 0.0.0.0:$PORT stade.wsgi
worker: celery worker --app stade.celery --concurrency 2 --loglevel info --without-gossip --without-mingle --without-heartbeat
