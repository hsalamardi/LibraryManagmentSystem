import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nta_library.settings')

app = Celery('nta_library')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'send-daily-notifications': {
        'task': 'books.tasks.send_daily_notifications',
        'schedule': 60.0 * 60.0 * 24.0,  # Run daily at midnight
        # 'schedule': crontab(hour=0, minute=0),  # Alternative: run at midnight
    },
    'send-due-date-reminders': {
        'task': 'books.tasks.send_due_date_reminders',
        'schedule': 60.0 * 60.0 * 24.0,  # Run daily
    },
    'cleanup-expired-reservations': {
        'task': 'books.tasks.cleanup_expired_reservations',
        'schedule': 60.0 * 60.0 * 24.0,  # Run daily
    },
    'generate-weekly-report': {
        'task': 'books.tasks.generate_weekly_report',
        'schedule': 60.0 * 60.0 * 24.0 * 7.0,  # Run weekly
        # 'schedule': crontab(hour=0, minute=0, day_of_week=1),  # Alternative: run every Monday
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')