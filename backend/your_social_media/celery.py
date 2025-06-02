"""
Celery configuration for your_social_media project.
"""
import os
import logging
from celery import Celery
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_social_media.settings')

# Import environment loader to ensure variables are available
try:
    import celery_env_loader
    logger.info("✅ Celery environment loader imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import celery_env_loader: {e}")

# Force Django setup to ensure settings are loaded
import django
django.setup()

app = Celery('your_social_media')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Log environment variables status when Celery starts
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Log API keys status when Celery worker starts"""
    logger.info("=== CELERY WORKER ENVIRONMENT CHECK ===")
    
    # Check environment variables directly
    groq_env = os.environ.get('GROQ_API_KEY', '')
    google_env = os.environ.get('GOOGLE_API_KEY', '')
    openai_env = os.environ.get('OPENAI_API_KEY', '')
    
    logger.info(f"GROQ_API_KEY from os.environ: {'✅ SET' if groq_env else '❌ NOT SET'} (length: {len(groq_env)})")
    logger.info(f"GOOGLE_API_KEY from os.environ: {'✅ SET' if google_env else '❌ NOT SET'} (length: {len(google_env)})")
    logger.info(f"OPENAI_API_KEY from os.environ: {'✅ SET' if openai_env else '❌ NOT SET'} (length: {len(openai_env)})")
    
    # Check Django settings
    try:
        from django.conf import settings
        groq_settings = getattr(settings, 'GROQ_API_KEY', '')
        google_settings = getattr(settings, 'GOOGLE_API_KEY', '')
        openai_settings = getattr(settings, 'OPENAI_API_KEY', '')
        
        logger.info(f"GROQ_API_KEY from settings: {'✅ SET' if groq_settings else '❌ NOT SET'} (length: {len(groq_settings)})")
        logger.info(f"GOOGLE_API_KEY from settings: {'✅ SET' if google_settings else '❌ NOT SET'} (length: {len(google_settings)})")
        logger.info(f"OPENAI_API_KEY from settings: {'✅ SET' if openai_settings else '❌ NOT SET'} (length: {len(openai_settings)})")
        
        # Show preview of keys for debugging
        if groq_env:
            logger.info(f"GROQ key preview (env): {groq_env[:8]}...{groq_env[-4:]}")
        if groq_settings:
            logger.info(f"GROQ key preview (settings): {groq_settings[:8]}...{groq_settings[-4:]}")
            
    except Exception as e:
        logger.error(f"Error checking Django settings in Celery: {e}")
    
    logger.info("=== END CELERY ENVIRONMENT CHECK ===")

# Ensure environment variables are available to tasks
@app.task(bind=True)
def debug_env_vars(self):
    """Debug task to check environment variables in Celery worker"""
    import os
    from django.conf import settings
    
    result = {
        'worker_id': self.request.id,
        'env_vars': {
            'GROQ_API_KEY': '✅ SET' if os.environ.get('GROQ_API_KEY') else '❌ NOT SET',
            'GOOGLE_API_KEY': '✅ SET' if os.environ.get('GOOGLE_API_KEY') else '❌ NOT SET',
            'OPENAI_API_KEY': '✅ SET' if os.environ.get('OPENAI_API_KEY') else '❌ NOT SET',
        },
        'settings_vars': {
            'GROQ_API_KEY': '✅ SET' if getattr(settings, 'GROQ_API_KEY', '') else '❌ NOT SET',
            'GOOGLE_API_KEY': '✅ SET' if getattr(settings, 'GOOGLE_API_KEY', '') else '❌ NOT SET',
            'OPENAI_API_KEY': '✅ SET' if getattr(settings, 'OPENAI_API_KEY', '') else '❌ NOT SET',
        }
    }
    
    return result 