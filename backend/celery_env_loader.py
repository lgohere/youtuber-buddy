"""
Environment loader for Celery workers to ensure API keys are available
"""
import os
import logging

logger = logging.getLogger(__name__)

def load_environment_for_celery():
    """
    Ensure all required environment variables are loaded for Celery workers
    This is especially important in containerized environments like Coolify
    """
    logger.info("Loading environment variables for Celery worker...")
    
    # List of required environment variables
    required_vars = [
        'GROQ_API_KEY',
        'GOOGLE_API_KEY', 
        'OPENAI_API_KEY',
        'SECRET_KEY',
        'POSTGRES_DB',
        'POSTGRES_USER', 
        'POSTGRES_PASSWORD',
        'POSTGRES_HOST',
        'REDIS_URL'
    ]
    
    missing_vars = []
    loaded_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            loaded_vars.append(var)
            # Log without exposing sensitive data
            if 'KEY' in var or 'PASSWORD' in var:
                logger.info(f"✅ {var}: loaded (length: {len(value)})")
            else:
                logger.info(f"✅ {var}: {value}")
        else:
            missing_vars.append(var)
            logger.warning(f"❌ {var}: NOT SET")
    
    logger.info(f"Environment check complete: {len(loaded_vars)} loaded, {len(missing_vars)} missing")
    
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
    
    return len(missing_vars) == 0

# Load environment when this module is imported
load_environment_for_celery() 