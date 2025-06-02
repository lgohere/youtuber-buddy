"""
Management command to test Groq API using the official groq library
"""
import os
import tempfile
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test Groq API using the official groq library'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== GROQ LIBRARY TEST ===\n'))
        
        # Get API key from different sources
        groq_from_settings = getattr(settings, 'GROQ_API_KEY', '')
        groq_from_environ = os.environ.get('GROQ_API_KEY', '')
        
        self.stdout.write(f"GROQ_API_KEY from settings: {'✅ FOUND' if groq_from_settings else '❌ NOT FOUND'} (length: {len(groq_from_settings)})")
        self.stdout.write(f"GROQ_API_KEY from os.environ: {'✅ FOUND' if groq_from_environ else '❌ NOT FOUND'} (length: {len(groq_from_environ)})")
        
        # Test with the groq library
        try:
            from groq import Groq
            self.stdout.write("✅ Groq library imported successfully")
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to import groq library: {e}"))
            return
        
        # Test with both keys
        for key_source, api_key in [("settings", groq_from_settings), ("environ", groq_from_environ)]:
            if not api_key:
                continue
                
            self.stdout.write(f'\n--- Testing with {key_source} key using groq library ---')
            
            try:
                # Initialize Groq client
                client = Groq(api_key=api_key)
                self.stdout.write(f"✅ Groq client initialized with {key_source} key")
                
                # Test 1: List models
                try:
                    models = client.models.list()
                    self.stdout.write(self.style.SUCCESS(f'✅ Models list: SUCCESS with {key_source} key'))
                    self.stdout.write(f"Available models: {len(models.data)}")
                    
                    # Show available models
                    for model in models.data[:3]:  # Show first 3 models
                        self.stdout.write(f"  - {model.id}")
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Models list: FAILED with {key_source} key - {str(e)}'))
                
                # Test 2: Create a simple audio file and test transcription
                try:
                    # Create a minimal audio file (silence) for testing
                    import wave
                    import struct
                    
                    # Create 1 second of silence at 16kHz mono
                    sample_rate = 16000
                    duration = 1  # 1 second
                    samples = [0] * (sample_rate * duration)
                    
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                        with wave.open(temp_audio.name, 'w') as wav_file:
                            wav_file.setnchannels(1)  # mono
                            wav_file.setsampwidth(2)  # 16-bit
                            wav_file.setframerate(sample_rate)
                            
                            # Write samples
                            for sample in samples:
                                wav_file.writeframes(struct.pack('<h', sample))
                        
                        # Test transcription using groq library
                        with open(temp_audio.name, 'rb') as audio_file:
                            transcription = client.audio.transcriptions.create(
                                file=("test.wav", audio_file.read()),
                                model="whisper-large-v3",
                                temperature=0.0,
                                response_format="text"
                            )
                            
                            self.stdout.write(self.style.SUCCESS(f'✅ Transcription: SUCCESS with {key_source} key'))
                            self.stdout.write(f'Transcription result: "{transcription[:100]}..."')
                        
                        # Cleanup
                        os.unlink(temp_audio.name)
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Transcription: FAILED with {key_source} key - {str(e)}'))
                    # Try to get more details about the error
                    if hasattr(e, 'response'):
                        self.stdout.write(f'Error response: {e.response}')
                    if hasattr(e, 'status_code'):
                        self.stdout.write(f'Status code: {e.status_code}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to initialize Groq client with {key_source} key: {str(e)}'))
        
        # Test 3: Compare with how it's used in the TranscriptionService
        self.stdout.write('\n--- Testing TranscriptionService initialization ---')
        try:
            from apps.transcriptions.services import TranscriptionService
            service = TranscriptionService()
            self.stdout.write(f"TranscriptionService groq_api_key: {'✅ SET' if service.groq_api_key else '❌ NOT SET'} (length: {len(service.groq_api_key) if service.groq_api_key else 0})")
            
            if service.groq_api_key:
                self.stdout.write(f"Service key preview: {service.groq_api_key[:8]}...{service.groq_api_key[-4:]}")
                
                # Compare with settings
                if service.groq_api_key == groq_from_settings:
                    self.stdout.write(self.style.SUCCESS("✅ Service key matches settings key"))
                else:
                    self.stdout.write(self.style.ERROR("❌ Service key differs from settings key"))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to test TranscriptionService: {str(e)}')) 