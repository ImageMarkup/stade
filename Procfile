release: python manage.py migrate
web: gunicorn --bind 0.0.0.0:$PORT --max-requests 100 stade.wsgi
worker: celery worker --app stade.celery --concurrency 1 --loglevel info --max-tasks-per-child 20 --without-gossip --without-mingle --without-heartbeat --hostname stade-worker@%h
