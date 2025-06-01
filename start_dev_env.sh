#!/bin/bash

echo "Starting Your Social Media Development Environment..."

# Activate virtual environment and start Django Development Server
echo "Starting Django server (backend)..."
(cd backend && source venv/bin/activate && python manage.py runserver) &
DJANGO_PID=$!
echo "Django server started with PID: $DJANGO_PID (Logs will appear above if any errors)"

# Start Vite Frontend Development Server
echo "Starting Vite frontend server..."
(cd frontend && npm run dev) &
VITE_PID=$!
echo "Vite server started with PID: $VITE_PID (Logs will appear above if any errors)"

# Activate virtual environment and start Celery Worker
echo "Starting Celery worker..."
(cd backend && source venv/bin/activate && celery -A your_social_media worker -l info) &
CELERY_PID=$!
echo "Celery worker started with PID: $CELERY_PID (Logs will appear above if any errors)"

echo ""
echo "-----------------------------------------------------"
echo "All services are starting in the background."
echo "-----------------------------------------------------"
echo "Useful URLs:"
echo "  Django Admin: http://127.0.0.1:8000/admin/"
echo "  API Root: http://127.0.0.1:8000/api/"
echo "  API Docs: http://127.0.0.1:8000/api/docs/"
echo "  Frontend: Vite will show its URL (usually http://localhost:5173 or http://localhost:3000)"
echo "-----------------------------------------------------"
echo "To stop the services, you can use their PIDs:"
echo "  Stop Django: kill $DJANGO_PID"
echo "  Stop Vite:   kill $VITE_PID"
echo "  Stop Celery: kill $CELERY_PID"
echo ""
echo "Alternatively, use 'pkill -f "manage.py runserver"', 'pkill -f vite', 'pkill -f "celery -A your_social_media worker"'"
echo "-----------------------------------------------------" 