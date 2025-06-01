"""
Django management command to check system status.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.transcriptions.models import Transcription
from apps.content_generation.models import ContentGeneration
import redis
import requests
import logging
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check system status and configuration'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 VERIFICAÇÃO DO STATUS DO SISTEMA')
        )
        self.stdout.write('=' * 50)

        # 1. Database Status
        self.check_database()
        
        # 2. Redis Status
        self.check_redis()
        
        # 3. API Keys
        self.check_api_keys()
        
        # 4. Transcription Stats
        self.check_transcription_stats()
        
        # 5. Content Generation Stats
        self.check_content_generation_stats()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Verificação completa!'))

    def check_database(self):
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📊 STATUS DO BANCO DE DADOS'))
        self.stdout.write('-' * 30)
        
        try:
            # Test database connection
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            self.stdout.write(self.style.SUCCESS('✅ Conexão com banco: OK'))
            
            # Count records
            transcription_count = Transcription.objects.count()
            content_count = ContentGeneration.objects.count()
            
            self.stdout.write(f'📝 Transcrições: {transcription_count}')
            self.stdout.write(f'🎯 Gerações de conteúdo: {content_count}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro no banco: {e}'))

    def check_redis(self):
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('🔴 STATUS DO REDIS'))
        self.stdout.write('-' * 20)
        
        try:
            r = redis.from_url(settings.CELERY_BROKER_URL)
            r.ping()
            self.stdout.write(self.style.SUCCESS('✅ Redis: Conectado'))
            
            # Check queue info
            info = r.info()
            self.stdout.write(f'📊 Versão: {info.get("redis_version", "N/A")}')
            self.stdout.write(f'💾 Memória usada: {info.get("used_memory_human", "N/A")}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Redis: {e}'))
            self.stdout.write('💡 Inicie Redis: brew services start redis')

    def check_api_keys(self):
        """Check API keys configuration"""
        self.stdout.write(self.style.HTTP_INFO('\n=== API KEYS STATUS ==='))
        
        # Check environment variables directly
        groq_env = os.environ.get('GROQ_API_KEY', '')
        google_env = os.environ.get('GOOGLE_API_KEY', '')
        openai_env = os.environ.get('OPENAI_API_KEY', '')
        
        self.stdout.write(f"GROQ_API_KEY from os.environ: {'✅ SET' if groq_env else '❌ NOT SET'} (length: {len(groq_env)})")
        self.stdout.write(f"GOOGLE_API_KEY from os.environ: {'✅ SET' if google_env else '❌ NOT SET'} (length: {len(google_env)})")
        self.stdout.write(f"OPENAI_API_KEY from os.environ: {'✅ SET' if openai_env else '❌ NOT SET'} (length: {len(openai_env)})")
        
        # Check Django settings
        groq_settings = getattr(settings, 'GROQ_API_KEY', '')
        google_settings = getattr(settings, 'GOOGLE_API_KEY', '')
        openai_settings = getattr(settings, 'OPENAI_API_KEY', '')
        
        self.stdout.write(f"GROQ_API_KEY from settings: {'✅ SET' if groq_settings else '❌ NOT SET'} (length: {len(groq_settings)})")
        self.stdout.write(f"GOOGLE_API_KEY from settings: {'✅ SET' if google_settings else '❌ NOT SET'} (length: {len(google_settings)})")
        self.stdout.write(f"OPENAI_API_KEY from settings: {'✅ SET' if openai_settings else '❌ NOT SET'} (length: {len(openai_settings)})")
        
        # Test Groq API if key is available
        if groq_settings:
            self.stdout.write('\n--- Testing Groq API ---')
            try:
                import requests
                headers = {'Authorization': f'Bearer {groq_settings}'}
                response = requests.get('https://api.groq.com/openai/v1/models', headers=headers, timeout=10)
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS('✅ Groq API: Working'))
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Groq API: Error {response.status_code} - {response.text}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Groq API: Exception - {str(e)}'))
        else:
            self.stdout.write(self.style.ERROR('❌ Groq API: No key available for testing'))
        
        # Show all environment variables starting with API or KEY (for debug)
        self.stdout.write('\n--- All API/KEY Environment Variables ---')
        for key, value in os.environ.items():
            if 'API' in key.upper() or 'KEY' in key.upper():
                masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                self.stdout.write(f"{key}: {masked_value} (length: {len(value)})")

    def check_transcription_stats(self):
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📝 ESTATÍSTICAS DE TRANSCRIÇÕES'))
        self.stdout.write('-' * 35)
        
        stats = {
            'pending': Transcription.objects.filter(status='pending').count(),
            'processing': Transcription.objects.filter(status='processing').count(),
            'completed': Transcription.objects.filter(status='completed').count(),
            'failed': Transcription.objects.filter(status='failed').count(),
        }
        
        for status, count in stats.items():
            if status == 'pending' and count > 0:
                self.stdout.write(self.style.WARNING(f'⏳ {status.title()}: {count}'))
            elif status == 'failed' and count > 0:
                self.stdout.write(self.style.ERROR(f'❌ {status.title()}: {count}'))
            elif status == 'completed':
                self.stdout.write(self.style.SUCCESS(f'✅ {status.title()}: {count}'))
            else:
                self.stdout.write(f'🔄 {status.title()}: {count}')

        # Source type breakdown
        self.stdout.write('')
        self.stdout.write('📊 Por tipo de fonte:')
        for source_type in ['youtube', 'audio_upload', 'video_upload']:
            count = Transcription.objects.filter(source_type=source_type).count()
            self.stdout.write(f'   {source_type}: {count}')

    def check_content_generation_stats(self):
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('🎯 ESTATÍSTICAS DE GERAÇÃO DE CONTEÚDO'))
        self.stdout.write('-' * 45)
        
        stats = {
            'pending': ContentGeneration.objects.filter(status='pending').count(),
            'processing': ContentGeneration.objects.filter(status='processing').count(),
            'completed': ContentGeneration.objects.filter(status='completed').count(),
            'failed': ContentGeneration.objects.filter(status='failed').count(),
        }
        
        for status, count in stats.items():
            if status == 'pending' and count > 0:
                self.stdout.write(self.style.WARNING(f'⏳ {status.title()}: {count}'))
            elif status == 'failed' and count > 0:
                self.stdout.write(self.style.ERROR(f'❌ {status.title()}: {count}'))
            elif status == 'completed':
                self.stdout.write(self.style.SUCCESS(f'✅ {status.title()}: {count}'))
            else:
                self.stdout.write(f'🔄 {status.title()}: {count}')

        # Content type breakdown
        self.stdout.write('')
        self.stdout.write('📊 Por tipo de conteúdo:')
        for content_type in ['titles', 'description', 'chapters', 'complete']:
            count = ContentGeneration.objects.filter(content_type=content_type).count()
            self.stdout.write(f'   {content_type}: {count}') 