#!/usr/bin/env bash
set -euo pipefail

# Apply all pending migrations on each boot.
python manage.py migrate --noinput

# Replit exposes the service port via $PORT.
exec gunicorn django_finances.wsgi:application \
  --bind 0.0.0.0:${PORT:-5000} \
  --workers 3 \
  --timeout 60 \
  --forwarded-allow-ips='*'
