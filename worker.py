import os
from celery_worker import celery

if __name__ == '__main__':
    args = [
        'worker',
        '--loglevel=info',
        '-P', 'gevent',  # Use gevent pool
    ]
    celery.worker_main(args)