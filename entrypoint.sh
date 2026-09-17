#!/bin/sh
set -e

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Iniciando Daphne..."
exec daphne -b 0.0.0.0 -p 8080 core.asgi:application