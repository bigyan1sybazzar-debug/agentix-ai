#!/bin/bash
set -e

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start gunicorn
exec gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120
