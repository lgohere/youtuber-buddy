"""
Management command to test environment variables loading
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test environment variables loading'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== ENVIRONMENT VARIABLES TEST ===\n'))
        
        # Test direct os.environ access
        self.stdout.write('--- Direct os.environ access ---')
        groq_direct = os.environ.get('GROQ_API_KEY', '')
        google_direct = os.environ.get('GOOGLE_API_KEY', '')
        openai_direct = os.environ.get('OPENAI_API_KEY', '')
        
        self.stdout.write(f"GROQ_API_KEY: {'✅ FOUND' if groq_direct else '❌ NOT FOUND'} (length: {len(groq_direct)})")
        self.stdout.write(f"GOOGLE_API_KEY: {'✅ FOUND' if google_direct else '❌ NOT FOUND'} (length: {len(google_direct)})")
        self.stdout.write(f"OPENAI_API_KEY: {'✅ FOUND' if openai_direct else '❌ NOT FOUND'} (length: {len(openai_direct)})")
        
        # Test Django settings
        self.stdout.write('\n--- Django settings access ---')
        groq_settings = getattr(settings, 'GROQ_API_KEY', '')
        google_settings = getattr(settings, 'GOOGLE_API_KEY', '')
        openai_settings = getattr(settings, 'OPENAI_API_KEY', '')
        
        self.stdout.write(f"settings.GROQ_API_KEY: {'✅ FOUND' if groq_settings else '❌ NOT FOUND'} (length: {len(groq_settings)})")
        self.stdout.write(f"settings.GOOGLE_API_KEY: {'✅ FOUND' if google_settings else '❌ NOT FOUND'} (length: {len(google_settings)})")
        self.stdout.write(f"settings.OPENAI_API_KEY: {'✅ FOUND' if openai_settings else '❌ NOT FOUND'} (length: {len(openai_settings)})")
        
        # Show first and last 4 chars of keys for verification
        if groq_direct:
            self.stdout.write(f"GROQ key preview: {groq_direct[:8]}...{groq_direct[-4:]}")
        if groq_settings:
            self.stdout.write(f"GROQ settings preview: {groq_settings[:8]}...{groq_settings[-4:]}")
            
        # Test Groq API directly
        if groq_direct:
            self.stdout.write('\n--- Testing Groq API ---')
            try:
                import requests
                headers = {'Authorization': f'Bearer {groq_direct}'}
                response = requests.get('https://api.groq.com/openai/v1/models', headers=headers, timeout=10)
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS('✅ Groq API test: SUCCESS'))
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Groq API test: FAILED - {response.status_code}'))
                    self.stdout.write(f'Response: {response.text[:200]}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Groq API test: EXCEPTION - {str(e)}'))
        
        # Show all environment variables for debug
        self.stdout.write('\n--- All Environment Variables (filtered) ---')
        for key in sorted(os.environ.keys()):
            if any(keyword in key.upper() for keyword in ['API', 'KEY', 'GROQ', 'GOOGLE', 'OPENAI', 'SECRET']):
                value = os.environ[key]
                if len(value) > 12:
                    masked = f"{value[:4]}...{value[-4:]}"
                else:
                    masked = "***"
                self.stdout.write(f"{key}: {masked} (len: {len(value)})") 