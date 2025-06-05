from celery import Celery

# Configure broker URL (e.g., Redis).
BROKER_URL = 'redis://localhost:6379/0'
RESULT_BACKEND_URL = 'redis://localhost:6379/1' # For storing task results

celery_app = Celery('thefacebookeye.scheduler',
                    broker=BROKER_URL,
                    backend=RESULT_BACKEND_URL,
                    include=['scheduler.tasks'])

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # beat_schedule={
    #     'run-data-collection-every-hour': {
    #         'task': 'scheduler.tasks.collect_data_task',
    #         'schedule': 3600.0,
    #     },
    # }
)

if __name__ == '__main__':
    print("Celery app configured. To run a worker: celery -A scheduler.celery_app worker -l INFO")
    print("Or for the beat scheduler (if schedules are defined): celery -A scheduler.celery_app beat -l INFO")
