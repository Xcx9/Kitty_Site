#!/bin/sh
set -e
cd "$(dirname "$0")"

PORT="${PORT:-8000}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

exec daphne -b 0.0.0.0 -p "$PORT" catdjango.asgi:application
