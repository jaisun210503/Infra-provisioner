from celery import Celery

# Create Celery instance with broker URL
celery_app = Celery(
    "infrautomater",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Additional configuration
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
)

# Auto-discover tasks in tasks package
celery_app.autodiscover_tasks(["celery_app.tasks"])