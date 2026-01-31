#!/bin/sh
set -e

#apply migrations and collectstatic
echo "run migrations"
python manage.py migrate --noinput

exec "$@"