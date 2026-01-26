# Celery Configuration

# Broker URL (Redis)
broker_url = "redis://localhost:6379/0"

# Result backend (Redis)
result_backend = "redis://localhost:6379/0"

# Task serialization
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

# Timezone
timezone = "UTC"
enable_utc = True

# Task settings
task_track_started = True
task_time_limit = 600  # 10 minutes max per task

# Retry settings
task_acks_late = True
task_reject_on_worker_lost = True
