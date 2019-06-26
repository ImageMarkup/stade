from celery import Celery
import os

app = Celery("stade", broker=os.environ.get("CLOUDAMQP_URL"), backend="rpc", broker_pool_limit=1)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
