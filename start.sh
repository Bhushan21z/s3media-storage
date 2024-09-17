#!/bin/bash

# Start Celery worker in the background
celery -A celery_worker.celery worker --loglevel=info &

# Start Gunicorn server
gunicorn app:app