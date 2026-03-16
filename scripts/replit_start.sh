#!/usr/bin/env bash
set -euo pipefail

# Install dependencies into the Replit environment.
python -m pip install --upgrade pip
pip install -r requirements.txt

# Apply DB/schema and static assets on each boot.
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Replit exposes the service port via $PORT.
exec gunicorn django_finances.wsgi:application --bind 0.0.0.0:${PORT:-8000}

