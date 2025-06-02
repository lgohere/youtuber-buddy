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

# Função para exportar variáveis de ambiente explicitamente
export_env_vars() {
    echo "Exporting environment variables explicitly..."
    
    # Export API keys explicitly
    if [ -n "$GROQ_API_KEY" ]; then
        export GROQ_API_KEY="$GROQ_API_KEY"
        echo "✅ GROQ_API_KEY exported (length: ${#GROQ_API_KEY})"
    else
        echo "❌ GROQ_API_KEY not found"
    fi
    
    if [ -n "$GOOGLE_API_KEY" ]; then
        export GOOGLE_API_KEY="$GOOGLE_API_KEY"
        echo "✅ GOOGLE_API_KEY exported (length: ${#GOOGLE_API_KEY})"
    else
        echo "❌ GOOGLE_API_KEY not found"
    fi
    
    if [ -n "$OPENAI_API_KEY" ]; then
        export OPENAI_API_KEY="$OPENAI_API_KEY"
        echo "✅ OPENAI_API_KEY exported (length: ${#OPENAI_API_KEY})"
    else
        echo "❌ OPENAI_API_KEY not found"
    fi
    
    # Export other important variables
    export SECRET_KEY="${SECRET_KEY:-}"
    export DEBUG="${DEBUG:-False}"
    export POSTGRES_DB="${POSTGRES_DB:-}"
    export POSTGRES_USER="${POSTGRES_USER:-}"
    export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
    export POSTGRES_HOST="${POSTGRES_HOST:-db}"
    export REDIS_URL="${REDIS_URL:-}"
    
    echo "Environment variables export complete."
}

# Export environment variables
export_env_vars

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

# Test Groq API directly
echo "Testing Groq API directly..."
python manage.py test_groq_direct

# Test Groq API using official library
echo "Testing Groq API using official library..."
python manage.py test_groq_library

# Verificar se é worker do Celery
if [ "$1" = "celery" ]; then
    echo "Starting Celery worker with explicit environment..."
    echo "GROQ_API_KEY available: ${GROQ_API_KEY:+YES (length: ${#GROQ_API_KEY})} ${GROQ_API_KEY:-NO}"
    echo "GOOGLE_API_KEY available: ${GOOGLE_API_KEY:+YES (length: ${#GOOGLE_API_KEY})} ${GOOGLE_API_KEY:-NO}"
    
    # Run environment loader for Celery
    echo "Running Celery environment loader..."
    python load_env_for_celery.py
    
    if [ $? -ne 0 ]; then
        echo "❌ Environment loader failed! Celery worker may not function correctly."
        echo "This is likely the cause of Groq API authentication errors."
    else
        echo "✅ Environment loader passed!"
    fi
    
    # Start Celery with explicit environment
    exec env \
        GROQ_API_KEY="$GROQ_API_KEY" \
        GOOGLE_API_KEY="$GOOGLE_API_KEY" \
        OPENAI_API_KEY="$OPENAI_API_KEY" \
        SECRET_KEY="$SECRET_KEY" \
        DEBUG="$DEBUG" \
        POSTGRES_DB="$POSTGRES_DB" \
        POSTGRES_USER="$POSTGRES_USER" \
        POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        POSTGRES_HOST="$POSTGRES_HOST" \
        REDIS_URL="$REDIS_URL" \
        celery -A your_social_media worker -l info --concurrency=2
        
elif [ "$1" = "celery-beat" ]; then
    echo "Starting Celery beat with explicit environment..."
    
    # Run environment loader for Celery beat
    echo "Running Celery environment loader..."
    python load_env_for_celery.py
    
    exec env \
        GROQ_API_KEY="$GROQ_API_KEY" \
        GOOGLE_API_KEY="$GOOGLE_API_KEY" \
        OPENAI_API_KEY="$OPENAI_API_KEY" \
        SECRET_KEY="$SECRET_KEY" \
        DEBUG="$DEBUG" \
        POSTGRES_DB="$POSTGRES_DB" \
        POSTGRES_USER="$POSTGRES_USER" \
        POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        POSTGRES_HOST="$POSTGRES_HOST" \
        REDIS_URL="$REDIS_URL" \
        celery -A your_social_media beat -l info
else
    # Test Celery environment (only for Django server, not for workers)
    echo "Testing Celery environment..."
    python manage.py test_celery_env
    
    echo "Starting Django server optimized for 2GB uploads..."
    exec gunicorn your_social_media.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 2 \
        --timeout 7200 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --limit-request-line 8192 \
        --limit-request-field_size 32768 \
        --access-logfile - \
        --error-logfile -
fi 