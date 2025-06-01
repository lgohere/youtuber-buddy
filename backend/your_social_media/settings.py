"""
Django settings for your_social_media project.
"""

import os
import environ
from pathlib import Path
import logging

# Instantiate logger early to be available throughout the file
logger = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, False),
    DOMAIN_NAME=(str, 'localhost')
)

# Read .env file only if DEBUG is True and DJANGO_SETTINGS_MODULE is not set (typical for local dev)
# Corrected DEBUG check using env('DEBUG') as it might not be set in os.environ yet
IS_DEBUG_MODE = env('DEBUG') # Read DEBUG status early

if IS_DEBUG_MODE and not os.environ.get('DJANGO_SETTINGS_MODULE'):
    env_file_path_root = os.path.join(BASE_DIR.parent.parent, '.env')
    env_file_path_backend = os.path.join(BASE_DIR.parent, '.env')
    if os.path.exists(env_file_path_root):
        logger.info(f"Attempting to load .env file from project root: {env_file_path_root}")
        environ.Env.read_env(env_file_path_root)
        logger.info("Loaded .env file from project root for local development.")
    elif os.path.exists(env_file_path_backend):
        logger.info(f"Attempting to load .env file from backend directory: {env_file_path_backend}")
        environ.Env.read_env(env_file_path_backend)
        logger.info("Loaded .env file from backend directory for local development.")
    else:
        logger.info("No .env file found for local development, relying on system env vars or defaults.")
else:
    if not IS_DEBUG_MODE:
        logger.info("Running in PRODUCTION (DEBUG=False). .env files will not be loaded by settings.py. Coolify variables should be used.")
    if os.environ.get('DJANGO_SETTINGS_MODULE'):
        logger.info(f"DJANGO_SETTINGS_MODULE ({os.environ.get('DJANGO_SETTINGS_MODULE')}) is set. .env files will not be loaded by settings.py. Coolify variables should be used.")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG is already read into IS_DEBUG_MODE, use that or read again if needed
DEBUG = IS_DEBUG_MODE # or DEBUG = env('DEBUG') if you prefer to read it again here

# Domain Name
DOMAIN_NAME = env('DOMAIN_NAME')

# Allowed Hosts
if DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'backend', DOMAIN_NAME]
else:
    ALLOWED_HOSTS = [DOMAIN_NAME, f'www.{DOMAIN_NAME}', 'api.texts.com.br', 'yt.texts.com.br']

# Add hosts from environment variable if any, for flexibility
ALLOWED_HOSTS.extend(env.list('ALLOWED_HOSTS_EXTRA', default=[]))

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'django_filters',
]

LOCAL_APPS = [
    'apps.users',
    'apps.transcriptions',
    'apps.content_generation',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'your_social_media.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates', BASE_DIR.parent / 'frontend' / 'dist'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'your_social_media.wsgi.application'

# Database
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': env.db_url('DATABASE_URL')
    }
    DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('POSTGRES_DB', default='youtuber_buddy'),
            'USER': env('POSTGRES_USER', default='postgres'),
            'PASSWORD': env('POSTGRES_PASSWORD', default='postgres'),
            'HOST': env('POSTGRES_HOST', default='db'),
            'PORT': env('POSTGRES_PORT', default='5432'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR.parent / 'frontend' / 'dist' / 'assets',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS Settings
if DEBUG:
    CORS_ALLOWED_ORIGINS = [
        f"http://{DOMAIN_NAME}",
        f"https://{DOMAIN_NAME}",
        f"http://localhost:3000",
        f"http://127.0.0.1:3000",
        f"http://localhost:8080",
        f"http://127.0.0.1:8080",
    ]
    if env('CORS_ALLOW_ALL_ORIGINS_DEV', default=False):
        CORS_ALLOW_ALL_ORIGINS = True
    else:
        CORS_ALLOW_ALL_ORIGINS = False
else:
    CORS_ALLOWED_ORIGINS = [
        f"https://{DOMAIN_NAME}",
        f"https://www.{DOMAIN_NAME}",
        "https://yt.texts.com.br",  # Frontend domain
        "https://api.texts.com.br",  # API domain
    ]

CORS_ALLOWED_ORIGINS.extend(env.list('CORS_ALLOWED_ORIGINS_EXTRA', default=[]))

CORS_ALLOW_CREDENTIALS = True

# CSRF Trusted Origins
if DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        f"http://{DOMAIN_NAME}",
        f"https://{DOMAIN_NAME}",
        f"http://localhost:3000",
        f"http://127.0.0.1:3000",
        f"http://localhost:8080",
        f"http://127.0.0.1:8080",
    ]
else:
    CSRF_TRUSTED_ORIGINS = [
        f"https://{DOMAIN_NAME}",
        f"https://www.{DOMAIN_NAME}",
        "https://yt.texts.com.br",  # Frontend domain
        "https://api.texts.com.br",  # API domain
    ]

CSRF_TRUSTED_ORIGINS.extend(env.list('CSRF_TRUSTED_ORIGINS_EXTRA', default=[]))

# CORS_ALLOWED_ORIGIN_REGEXES: Remove or refine for production
CORS_ALLOWED_ORIGIN_REGEXES = []
if DEBUG:
    CORS_ALLOWED_ORIGIN_REGEXES.extend([
        r"^http://localhost:\d+$",
        r"^http://127\.0\.0\.1:\d+$",
    ])

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Your Social Media API',
    'DESCRIPTION': 'API para geração de conteúdo YouTube com IA',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Celery Configuration
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
if not CELERY_BROKER_URL.startswith('redis://'):
    CELERY_BROKER_URL = f"redis://{CELERY_BROKER_URL}"

CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')
if not CELERY_RESULT_BACKEND.startswith('redis://'):
    CELERY_RESULT_BACKEND = f"redis://{CELERY_RESULT_BACKEND}"

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# AI APIs Configuration
if DEBUG:
    # In DEBUG mode, allow reading from .env via django-environ for local development
    GROQ_API_KEY = env('GROQ_API_KEY', default='')
    GOOGLE_API_KEY = env('GOOGLE_API_KEY', default='')
    OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
else:
    # In PRODUCTION (DEBUG=False), strictly use os.environ to ensure Coolify variables are used
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Debug: Log API key status (without exposing the actual keys)
logger.info(f"[SETTINGS] GROQ_API_KEY loaded: {'Yes' if GROQ_API_KEY else 'No'} (length: {len(GROQ_API_KEY) if GROQ_API_KEY else 0})")
logger.info(f"[SETTINGS] GOOGLE_API_KEY loaded: {'Yes' if GOOGLE_API_KEY else 'No'} (length: {len(GOOGLE_API_KEY) if GOOGLE_API_KEY else 0})")
logger.info(f"[SETTINGS] OPENAI_API_KEY loaded: {'Yes' if OPENAI_API_KEY else 'No'} (length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0})")

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 1024  # 1GB
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 1024  # 1GB

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Create logs directory
os.makedirs(BASE_DIR / 'logs', exist_ok=True) 