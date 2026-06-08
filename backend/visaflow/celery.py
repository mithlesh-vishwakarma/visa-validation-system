import os
from celery import Celery

# Set default Django settings module for celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaflow.settings')

app = Celery('visaflow')

# Config from django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in installed apps
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
