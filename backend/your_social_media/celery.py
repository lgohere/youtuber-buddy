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

@app.task(bind=True)
def test_groq_api_in_celery(self):
    """Test Groq API specifically within Celery worker context"""
    import os
    import requests
    from django.conf import settings
    from apps.transcriptions.services import TranscriptionService
    
    result = {
        'worker_id': self.request.id,
        'environment_check': {},
        'service_check': {},
        'api_test': {},
        'format_check': {}
    }
    
    # Test 1: Environment variables
    groq_key_env = os.environ.get('GROQ_API_KEY')
    groq_key_settings = getattr(settings, 'GROQ_API_KEY', None)
    
    result['environment_check'] = {
        'env_var': '✅ SET' if groq_key_env else '❌ NOT SET',
        'settings_var': '✅ SET' if groq_key_settings else '❌ NOT SET',
        'env_length': len(groq_key_env) if groq_key_env else 0,
        'settings_length': len(groq_key_settings) if groq_key_settings else 0
    }
    
    # Test 2: TranscriptionService
    try:
        service = TranscriptionService()
        if hasattr(service, 'groq_api_key') and service.groq_api_key:
            result['service_check'] = {
                'status': '✅ INITIALIZED',
                'key_length': len(service.groq_api_key),
                'key_preview': f"{service.groq_api_key[:8]}...{service.groq_api_key[-4:]}"
            }
        else:
            result['service_check'] = {'status': '❌ NOT INITIALIZED'}
    except Exception as e:
        result['service_check'] = {'status': f'❌ ERROR: {str(e)}'}
    
    # Test 3: Direct API test
    api_key = groq_key_env or groq_key_settings
    if api_key:
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                models = response.json()
                result['api_test'] = {
                    'status': '✅ SUCCESS',
                    'models_count': len(models.get('data', [])),
                    'first_model': models.get('data', [{}])[0].get('id', 'None') if models.get('data') else 'None'
                }
            else:
                result['api_test'] = {
                    'status': f'❌ FAILED',
                    'status_code': response.status_code,
                    'error': response.text[:200]
                }
        except Exception as e:
            result['api_test'] = {'status': f'❌ EXCEPTION: {str(e)}'}
    else:
        result['api_test'] = {'status': '❌ NO API KEY'}
    
    # Test 4: Format check
    if api_key:
        result['format_check'] = {
            'correct_prefix': api_key.startswith('gsk_'),
            'correct_length': len(api_key) == 56,
            'actual_length': len(api_key),
            'prefix': api_key[:4] if len(api_key) >= 4 else api_key
        }
    else:
        result['format_check'] = {'status': 'NO API KEY TO CHECK'}
    
    logger.info(f"Groq API test result: {result}")
    return result 