#!/usr/bin/env python3
"""
Script to ensure environment variables are loaded for Celery workers
This addresses the issue where Celery workers in Docker/Coolify don't inherit environment variables
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_environment_variables():
    """Load and verify environment variables for Celery"""
    logger.info("=== CELERY ENVIRONMENT LOADER ===")
    
    # Required environment variables
    required_vars = {
        'GROQ_API_KEY': 'Groq API key for transcription',
        'GOOGLE_API_KEY': 'Google AI API key for content generation', 
        'OPENAI_API_KEY': 'OpenAI API key (optional)',
        'SECRET_KEY': 'Django secret key',
        'POSTGRES_DB': 'PostgreSQL database name',
        'POSTGRES_USER': 'PostgreSQL username',
        'POSTGRES_PASSWORD': 'PostgreSQL password',
        'POSTGRES_HOST': 'PostgreSQL host',
        'REDIS_URL': 'Redis URL for Celery broker'
    }
    
    missing_vars = []
    loaded_vars = []
    
    for var_name, description in required_vars.items():
        value = os.environ.get(var_name)
        if value:
            loaded_vars.append(var_name)
            # Don't log sensitive values, just confirm they exist
            if 'KEY' in var_name or 'PASSWORD' in var_name:
                logger.info(f"✅ {var_name}: loaded (length: {len(value)})")
            else:
                logger.info(f"✅ {var_name}: {value}")
        else:
            missing_vars.append(var_name)
            logger.error(f"❌ {var_name}: NOT SET - {description}")
    
    logger.info(f"Environment check: {len(loaded_vars)} loaded, {len(missing_vars)} missing")
    
    if missing_vars:
        logger.error("CRITICAL: Missing environment variables will cause Celery tasks to fail!")
        logger.error("This is likely the root cause of Groq API authentication errors.")
        return False
    else:
        logger.info("✅ All required environment variables are available")
        return True

def export_vars_to_celery():
    """Explicitly export variables for Celery subprocess"""
    vars_to_export = [
        'GROQ_API_KEY',
        'GOOGLE_API_KEY', 
        'OPENAI_API_KEY',
        'SECRET_KEY',
        'DEBUG',
        'POSTGRES_DB',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD', 
        'POSTGRES_HOST',
        'REDIS_URL',
        'DJANGO_SETTINGS_MODULE'
    ]
    
    for var in vars_to_export:
        value = os.environ.get(var)
        if value:
            os.environ[var] = value
            logger.info(f"Exported {var} to environment")

if __name__ == "__main__":
    success = load_environment_variables()
    export_vars_to_celery()
    
    if not success:
        logger.error("Environment check failed!")
        sys.exit(1)
    else:
        logger.info("Environment check passed!")
        sys.exit(0) 