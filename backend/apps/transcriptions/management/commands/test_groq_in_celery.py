"""
Test Groq API specifically within Celery worker context
"""
import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.transcriptions.services import TranscriptionService


class Command(BaseCommand):
    help = 'Test Groq API within Celery worker context'

    def handle(self, *args, **options):
        self.stdout.write("=== TESTING GROQ API IN CELERY CONTEXT ===")
        
        # Test 1: Check environment variables
        self.stdout.write("\n1. Environment Variables Check:")
        groq_key_env = os.environ.get('GROQ_API_KEY')
        groq_key_settings = getattr(settings, 'GROQ_API_KEY', None)
        
        if groq_key_env:
            self.stdout.write(f"   ✅ GROQ_API_KEY from os.environ: {groq_key_env[:8]}...{groq_key_env[-4:]} (length: {len(groq_key_env)})")
        else:
            self.stdout.write("   ❌ GROQ_API_KEY not found in os.environ")
            
        if groq_key_settings:
            self.stdout.write(f"   ✅ GROQ_API_KEY from settings: {groq_key_settings[:8]}...{groq_key_settings[-4:]} (length: {len(groq_key_settings)})")
        else:
            self.stdout.write("   ❌ GROQ_API_KEY not found in settings")
        
        # Test 2: TranscriptionService initialization
        self.stdout.write("\n2. TranscriptionService Check:")
        try:
            service = TranscriptionService()
            if hasattr(service, 'groq_api_key') and service.groq_api_key:
                self.stdout.write(f"   ✅ TranscriptionService.groq_api_key: {service.groq_api_key[:8]}...{service.groq_api_key[-4:]} (length: {len(service.groq_api_key)})")
            else:
                self.stdout.write("   ❌ TranscriptionService.groq_api_key not set")
        except Exception as e:
            self.stdout.write(f"   ❌ Error initializing TranscriptionService: {e}")
        
        # Test 3: Direct API test
        self.stdout.write("\n3. Direct Groq API Test:")
        api_key = groq_key_env or groq_key_settings
        if api_key:
            try:
                # Test with a simple API call to check authentication
                headers = {"Authorization": f"Bearer {api_key}"}
                
                # Use models endpoint to test authentication
                response = requests.get(
                    "https://api.groq.com/openai/v1/models",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    models = response.json()
                    self.stdout.write(f"   ✅ API Authentication successful! Found {len(models.get('data', []))} models")
                    
                    # Show available models
                    for model in models.get('data', [])[:3]:  # Show first 3 models
                        self.stdout.write(f"      - {model.get('id', 'Unknown')}")
                        
                elif response.status_code == 401:
                    self.stdout.write(f"   ❌ API Authentication failed: {response.text}")
                else:
                    self.stdout.write(f"   ⚠️  API returned status {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.stdout.write(f"   ❌ Error testing API: {e}")
        else:
            self.stdout.write("   ❌ No API key available for testing")
        
        # Test 4: Check if key format is correct
        self.stdout.write("\n4. API Key Format Check:")
        if api_key:
            if api_key.startswith('gsk_'):
                self.stdout.write("   ✅ API key has correct 'gsk_' prefix")
            else:
                self.stdout.write(f"   ❌ API key has incorrect prefix: '{api_key[:4]}...'")
                
            if len(api_key) == 56:
                self.stdout.write("   ✅ API key has correct length (56 characters)")
            else:
                self.stdout.write(f"   ❌ API key has incorrect length: {len(api_key)} (expected 56)")
        
        self.stdout.write("\n=== TEST COMPLETE ===") 