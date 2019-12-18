import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stade.settings.production')

app = Celery('stade', config_source='django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
