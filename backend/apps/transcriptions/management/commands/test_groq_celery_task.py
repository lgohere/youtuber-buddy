"""
Test Groq API by running a Celery task
"""
from django.core.management.base import BaseCommand
from your_social_media.celery import test_groq_api_in_celery


class Command(BaseCommand):
    help = 'Test Groq API by running a Celery task'

    def handle(self, *args, **options):
        self.stdout.write("=== TESTING GROQ API VIA CELERY TASK ===")
        
        try:
            # Execute the Celery task
            self.stdout.write("Sending test task to Celery worker...")
            result = test_groq_api_in_celery.delay()
            
            self.stdout.write(f"Task ID: {result.id}")
            self.stdout.write("Waiting for result...")
            
            # Wait for result with timeout
            task_result = result.get(timeout=30)
            
            self.stdout.write("\n=== TASK RESULT ===")
            
            # Environment Check
            env_check = task_result.get('environment_check', {})
            self.stdout.write(f"\n1. Environment Variables:")
            self.stdout.write(f"   - os.environ: {env_check.get('env_var', 'Unknown')} (length: {env_check.get('env_length', 0)})")
            self.stdout.write(f"   - settings: {env_check.get('settings_var', 'Unknown')} (length: {env_check.get('settings_length', 0)})")
            
            # Service Check
            service_check = task_result.get('service_check', {})
            self.stdout.write(f"\n2. TranscriptionService:")
            self.stdout.write(f"   - Status: {service_check.get('status', 'Unknown')}")
            if 'key_length' in service_check:
                self.stdout.write(f"   - Key length: {service_check.get('key_length')}")
                self.stdout.write(f"   - Key preview: {service_check.get('key_preview')}")
            
            # API Test
            api_test = task_result.get('api_test', {})
            self.stdout.write(f"\n3. API Test:")
            self.stdout.write(f"   - Status: {api_test.get('status', 'Unknown')}")
            if 'models_count' in api_test:
                self.stdout.write(f"   - Models found: {api_test.get('models_count')}")
                self.stdout.write(f"   - First model: {api_test.get('first_model')}")
            elif 'status_code' in api_test:
                self.stdout.write(f"   - HTTP Status: {api_test.get('status_code')}")
                self.stdout.write(f"   - Error: {api_test.get('error', '')[:100]}...")
            
            # Format Check
            format_check = task_result.get('format_check', {})
            self.stdout.write(f"\n4. Format Check:")
            if 'correct_prefix' in format_check:
                prefix_status = "✅" if format_check.get('correct_prefix') else "❌"
                length_status = "✅" if format_check.get('correct_length') else "❌"
                self.stdout.write(f"   - Prefix 'gsk_': {prefix_status} (actual: {format_check.get('prefix', 'N/A')})")
                self.stdout.write(f"   - Length 56: {length_status} (actual: {format_check.get('actual_length', 0)})")
            else:
                self.stdout.write(f"   - {format_check.get('status', 'Unknown')}")
            
            self.stdout.write(f"\n=== WORKER ID: {task_result.get('worker_id', 'Unknown')} ===")
            
        except Exception as e:
            self.stdout.write(f"❌ Error executing task: {e}")
        
        self.stdout.write("\n=== TEST COMPLETE ===") 