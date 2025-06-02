"""
Management command to test Celery environment variables
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test Celery environment variables by running a debug task'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== CELERY ENVIRONMENT TEST ===\n'))
        
        # Test 1: Check if Celery is available
        try:
            from celery import current_app
            self.stdout.write("✅ Celery imported successfully")
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to import Celery: {e}"))
            return
        
        # Test 2: Check if debug task is available
        try:
            from your_social_media.celery import debug_env_vars
            self.stdout.write("✅ Debug task imported successfully")
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to import debug task: {e}"))
            return
        
        # Test 3: Check current environment in Django process
        self.stdout.write('\n--- Django Process Environment ---')
        groq_django = os.environ.get('GROQ_API_KEY', '')
        google_django = os.environ.get('GOOGLE_API_KEY', '')
        openai_django = os.environ.get('OPENAI_API_KEY', '')
        
        self.stdout.write(f"GROQ_API_KEY: {'✅ SET' if groq_django else '❌ NOT SET'} (length: {len(groq_django)})")
        self.stdout.write(f"GOOGLE_API_KEY: {'✅ SET' if google_django else '❌ NOT SET'} (length: {len(google_django)})")
        self.stdout.write(f"OPENAI_API_KEY: {'✅ SET' if openai_django else '❌ NOT SET'} (length: {len(openai_django)})")
        
        # Test 4: Execute Celery task to check worker environment
        self.stdout.write('\n--- Testing Celery Worker Environment ---')
        try:
            # Execute the debug task
            result = debug_env_vars.delay()
            self.stdout.write(f"Task submitted with ID: {result.id}")
            
            # Wait for result (with timeout)
            try:
                task_result = result.get(timeout=30)
                self.stdout.write("✅ Task completed successfully")
                
                self.stdout.write('\n--- Celery Worker Results ---')
                self.stdout.write(f"Worker ID: {task_result['worker_id']}")
                
                self.stdout.write('\nEnvironment Variables in Worker:')
                for key, status in task_result['env_vars'].items():
                    self.stdout.write(f"  {key}: {status}")
                
                self.stdout.write('\nDjango Settings in Worker:')
                for key, status in task_result['settings_vars'].items():
                    self.stdout.write(f"  {key}: {status}")
                
                # Check if all required vars are available in worker
                missing_env = [k for k, v in task_result['env_vars'].items() if '❌' in v]
                missing_settings = [k for k, v in task_result['settings_vars'].items() if '❌' in v]
                
                if not missing_env and not missing_settings:
                    self.stdout.write(self.style.SUCCESS('\n✅ All environment variables are available in Celery worker!'))
                else:
                    self.stdout.write(self.style.ERROR(f'\n❌ Missing variables in worker:'))
                    if missing_env:
                        self.stdout.write(f'  Environment: {missing_env}')
                    if missing_settings:
                        self.stdout.write(f'  Settings: {missing_settings}')
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Task execution failed: {e}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to submit task: {e}"))
        
        # Test 5: Test actual Groq API call from Celery
        self.stdout.write('\n--- Testing Groq API from Celery ---')
        try:
            from apps.transcriptions.tasks import process_audio_transcription
            self.stdout.write("✅ Transcription task imported successfully")
            
            # Note: We won't actually run this task as it requires a real transcription object
            self.stdout.write("ℹ️ Transcription task is available (not executed in test)")
            
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to import transcription task: {e}"))
        
        self.stdout.write('\n=== TEST COMPLETE ===')
        self.stdout.write('If you see ❌ for environment variables in the Celery worker,')
        self.stdout.write('the issue is that Celery is not receiving the environment variables from Coolify.')
        self.stdout.write('This confirms the root cause of the Groq API authentication failures.') 