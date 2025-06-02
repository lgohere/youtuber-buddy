"""
Management command to test Groq API directly
"""
import os
import requests
import tempfile
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test Groq API directly with a simple audio file'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== GROQ API DIRECT TEST ===\n'))
        
        # Get API key from different sources
        groq_from_settings = getattr(settings, 'GROQ_API_KEY', '')
        groq_from_environ = os.environ.get('GROQ_API_KEY', '')
        
        self.stdout.write(f"GROQ_API_KEY from settings: {'✅ FOUND' if groq_from_settings else '❌ NOT FOUND'} (length: {len(groq_from_settings)})")
        self.stdout.write(f"GROQ_API_KEY from os.environ: {'✅ FOUND' if groq_from_environ else '❌ NOT FOUND'} (length: {len(groq_from_environ)})")
        
        if groq_from_settings:
            self.stdout.write(f"Settings key preview: {groq_from_settings[:8]}...{groq_from_settings[-4:]}")
        if groq_from_environ:
            self.stdout.write(f"Environ key preview: {groq_from_environ[:8]}...{groq_from_environ[-4:]}")
            
        # Check if they're the same
        if groq_from_settings and groq_from_environ:
            if groq_from_settings == groq_from_environ:
                self.stdout.write(self.style.SUCCESS("✅ Both keys are identical"))
            else:
                self.stdout.write(self.style.ERROR("❌ Keys are different!"))
                self.stdout.write(f"Settings: {groq_from_settings[:20]}...")
                self.stdout.write(f"Environ:  {groq_from_environ[:20]}...")
        
        # Test with both keys
        for key_source, api_key in [("settings", groq_from_settings), ("environ", groq_from_environ)]:
            if not api_key:
                continue
                
            self.stdout.write(f'\n--- Testing with {key_source} key ---')
            
            # Test 1: Simple models endpoint
            try:
                headers = {'Authorization': f'Bearer {api_key}'}
                response = requests.get('https://api.groq.com/openai/v1/models', headers=headers, timeout=10)
                
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(f'✅ Models endpoint: SUCCESS with {key_source} key'))
                    models = response.json()
                    self.stdout.write(f"Available models: {len(models.get('data', []))}")
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Models endpoint: FAILED with {key_source} key - {response.status_code}'))
                    self.stdout.write(f'Response: {response.text[:200]}')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Models endpoint: EXCEPTION with {key_source} key - {str(e)}'))
            
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
                    
                    # Test transcription
                    headers = {'Authorization': f'Bearer {api_key}'}
                    
                    with open(temp_audio.name, 'rb') as audio_file:
                        files = {"file": ("test.wav", audio_file, "audio/wav")}
                        data = {
                            "model": "whisper-large-v3",
                            "temperature": 0.0,
                            "response_format": "text"
                        }
                        
                        response = requests.post(
                            'https://api.groq.com/openai/v1/audio/transcriptions',
                            headers=headers,
                            files=files,
                            data=data,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            self.stdout.write(self.style.SUCCESS(f'✅ Transcription endpoint: SUCCESS with {key_source} key'))
                            result = response.text
                            self.stdout.write(f'Transcription result: "{result[:100]}..."')
                        else:
                            self.stdout.write(self.style.ERROR(f'❌ Transcription endpoint: FAILED with {key_source} key - {response.status_code}'))
                            self.stdout.write(f'Response: {response.text[:200]}')
                    
                    # Cleanup
                    os.unlink(temp_audio.name)
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Transcription test: EXCEPTION with {key_source} key - {str(e)}'))
        
        # Test 3: Check for invisible characters or encoding issues
        if groq_from_settings:
            self.stdout.write('\n--- Checking for encoding issues ---')
            key_bytes = groq_from_settings.encode('utf-8')
            self.stdout.write(f"Key as bytes length: {len(key_bytes)}")
            self.stdout.write(f"Key as string length: {len(groq_from_settings)}")
            
            # Check for common invisible characters
            invisible_chars = ['\u200b', '\u200c', '\u200d', '\ufeff', '\u00a0']
            found_invisible = []
            for char in invisible_chars:
                if char in groq_from_settings:
                    found_invisible.append(char)
            
            if found_invisible:
                self.stdout.write(self.style.ERROR(f"❌ Found invisible characters: {found_invisible}"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ No invisible characters found"))
            
            # Check for leading/trailing whitespace
            if groq_from_settings != groq_from_settings.strip():
                self.stdout.write(self.style.ERROR("❌ Key has leading/trailing whitespace"))
                self.stdout.write(f"Original length: {len(groq_from_settings)}")
                self.stdout.write(f"Stripped length: {len(groq_from_settings.strip())}")
            else:
                self.stdout.write(self.style.SUCCESS("✅ No leading/trailing whitespace")) 