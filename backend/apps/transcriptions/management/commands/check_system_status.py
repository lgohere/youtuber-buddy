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
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('🔑 STATUS DAS API KEYS'))
        self.stdout.write('-' * 25)
        
        # GROQ API
        if settings.GROQ_API_KEY:
            self.stdout.write(self.style.SUCCESS('✅ GROQ API Key: Configurada'))
            # Test GROQ connection
            try:
                headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
                response = requests.get(
                    "https://api.groq.com/openai/v1/models", 
                    headers=headers, 
                    timeout=5
                )
                if response.status_code == 200:
                    self.stdout.write('🌐 GROQ API: Conectada')
                else:
                    self.stdout.write(self.style.WARNING('⚠️  GROQ API: Erro de conexão'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️  GROQ API: {e}'))
        else:
            self.stdout.write(self.style.ERROR('❌ GROQ API Key: Não configurada'))

        # Google API
        if settings.GOOGLE_API_KEY:
            self.stdout.write(self.style.SUCCESS('✅ Google API Key: Configurada'))
            # Test Google connection
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GOOGLE_API_KEY)
                model = genai.GenerativeModel('gemini-2.0-flash')
                self.stdout.write('🌐 Google AI: Conectada')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️  Google AI: {e}'))
        else:
            self.stdout.write(self.style.ERROR('❌ Google API Key: Não configurada'))

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