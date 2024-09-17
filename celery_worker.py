import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

def make_celery(app=None):
    redis_url = os.getenv('REDIS_URL')
    celery = Celery(
        'tasks',
        broker=redis_url,
        backend=redis_url,
        include=['tasks']
    )

    if app:
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        celery.Task = ContextTask

    return celery

celery = make_celery()
