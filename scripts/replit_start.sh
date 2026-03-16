#!/usr/bin/env bash
set -euo pipefail

# Sync DB schema directly from models, bypassing migration history conflicts.
python manage.py migrate --run-syncdb

# Replit exposes the service port via $PORT.
exec gunicorn django_finances.wsgi:application \
  --bind 0.0.0.0:${PORT:-5000} \
  --workers 3 \
  --timeout 60 \
  --forwarded-allow-ips='*'
