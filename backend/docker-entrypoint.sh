#!/bin/bash
set -e

# Função para aguardar o banco de dados
wait_for_db() {
    echo "Waiting for database..."
    while ! python manage.py check --database default; do
        echo "Database is unavailable - sleeping"
        sleep 1
    done
    echo "Database is up!"
}

# Aguardar banco de dados
wait_for_db

# Executar migrações
echo "Running migrations..."
python manage.py migrate --noinput

# Coletar arquivos estáticos
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Test environment variables
echo "Testing environment variables..."
python manage.py test_env_vars

# Verificar se é worker do Celery
if [ "$1" = "celery" ]; then
    echo "Starting Celery worker..."
    exec celery -A your_social_media worker -l info --concurrency=2
elif [ "$1" = "celery-beat" ]; then
    echo "Starting Celery beat..."
    exec celery -A your_social_media beat -l info
else
    echo "Starting Django server..."
    exec gunicorn your_social_media.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 2 \
        --timeout 300 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --access-logfile - \
        --error-logfile -
fi 