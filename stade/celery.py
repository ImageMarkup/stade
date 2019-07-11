import os

from celery import Celery

app = Celery('stade', broker=os.environ.get('CLOUDAMQP_URL'), backend='rpc', broker_pool_limit=1)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
