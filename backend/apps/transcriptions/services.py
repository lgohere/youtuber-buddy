"""
Services for transcription processing.
Migrated from original Streamlit application.
"""
import os
import re
import requests
import logging
import tempfile
import time
import math
from typing import Optional, Tuple, Dict, Any, List
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
import yt_dlp as youtube_dl
from bs4 import BeautifulSoup
import html
from .models import Transcription, TranscriptionSegment

logger = logging.getLogger(__name__)

# Constants from original app
GROQ_API_MAX_FILE_SIZE = 24 * 1024 * 1024  # 24 MB
MAX_RETRIES = 5
INITIAL_BACKOFF = 2
MAX_BACKOFF = 60
SEGMENT_DURATION_MS = 10 * 60 * 1000  # 10 minutes in milliseconds


class TranscriptionService:
    """Service for handling transcription operations."""
    
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
    
    def format_timestamp(self, timestamp_float: float) -> str:
        """Format the timestamp float into HH:MM:SS"""
        try:
            total_seconds = float(timestamp_float)
            hours, remainder = divmod(int(total_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        except Exception as e:
            logger.error(f"Erro ao formatar timestamp '{timestamp_float}': {e}")
            return "00:00"
    
    def sanitize_filename(self, filename: str) -> str:
        """Remove caracteres inválidos do nome do arquivo."""
        return re.sub(r'[\\/*?:"<>|]', "", filename)
    
    def validate_youtube_url(self, url: str) -> bool:
        """Validate YouTube URL format."""
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/live/[\w-]+',
        ]
        
        for pattern in youtube_patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def extract_youtube_transcript(self, video_url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Extract transcript and metadata from YouTube video."""
        try:
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'quiet': True,
                'no_warnings': True,
                'default_search': 'auto',
                'compat_opts': {'ffmpeg': 'false'},
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=False)
                title = info_dict.get('title', 'sem_titulo')
                upload_date_str = info_dict.get('upload_date', None)
                upload_date = None

                if upload_date_str:
                    try:
                        from datetime import datetime
                        upload_date = datetime.strptime(upload_date_str, "%Y%m%d").strftime("%d/%m/%Y")
                    except ValueError:
                        upload_date = upload_date_str

                # Get subtitles
                subtitles = info_dict.get('subtitles', {})
                automatic_captions = info_dict.get('automatic_captions', {})

                logger.info(f"Legendas disponíveis: {list(subtitles.keys())}")
                logger.info(f"Legendas automáticas disponíveis: {list(automatic_captions.keys())}")

                # Detect original language
                original_language = info_dict.get('language')
                if original_language:
                    logger.info(f"Idioma original detectado: {original_language}")

                selected_subs = None
                lang = None
                subtitle_type = None
                
                # Priority languages
                priority_languages = []
                
                if original_language:
                    priority_languages.append(original_language)
                
                common_languages = ['en', 'pt', 'pt-BR', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'zh', 'ru']
                for lang_code in common_languages:
                    if lang_code not in priority_languages:
                        priority_languages.append(lang_code)
                
                # Try manual subtitles first
                for lang_priority in priority_languages:
                    if lang_priority in subtitles:
                        selected_subs = subtitles[lang_priority]
                        lang = lang_priority
                        subtitle_type = "manual"
                        logger.info(f"Usando legenda manual em {lang_priority}")
                        break
                
                # Try automatic captions
                if not selected_subs:
                    for lang_priority in priority_languages:
                        if lang_priority in automatic_captions:
                            selected_subs = automatic_captions[lang_priority]
                            lang = lang_priority
                            subtitle_type = "automática"
                            logger.info(f"Usando legenda automática em {lang_priority}")
                            break
                
                # Fallback to any available subtitle
                if not selected_subs:
                    if subtitles:
                        lang, selected_subs = next(iter(subtitles.items()))
                        subtitle_type = "manual"
                        logger.info(f"Usando primeira legenda manual disponível: {lang}")
                    elif automatic_captions:
                        lang, selected_subs = next(iter(automatic_captions.items()))
                        subtitle_type = "automática"
                        logger.info(f"Usando primeira legenda automática disponível: {lang}")
                    else:
                        logger.error("Nenhuma legenda disponível")
                        return None, title, upload_date, None, None

                # Process subtitles
                for sub_format in selected_subs:
                    try:
                        transcript_url = sub_format.get('url')
                        if not transcript_url:
                            continue

                        transcript_response = requests.get(transcript_url)
                        if transcript_response.status_code == 200:
                            transcript_xml = transcript_response.content
                            transcript_soup = BeautifulSoup(transcript_xml, 'xml')
                            transcript_segments = transcript_soup.find_all('text') or transcript_soup.find_all('p')

                            if transcript_segments:
                                full_transcript = []
                                for segment in transcript_segments:
                                    timestamp = segment.get('start', '0')
                                    text = segment.get_text().strip()
                                    if text:
                                        # Decode HTML entities
                                        text = html.unescape(text)
                                        formatted_timestamp = self.format_timestamp(timestamp)
                                        full_transcript.append(f"{formatted_timestamp} {text}")

                                if full_transcript:
                                    return '\n'.join(full_transcript), title, upload_date, lang, subtitle_type

                    except Exception as e:
                        logger.error(f"Erro ao processar formato de legenda: {e}")

                return None, title, upload_date, lang, subtitle_type

        except Exception as e:
            logger.error(f"Erro ao extrair transcrição do YouTube: {e}")
            return None, None, None, None, None
    
    def extract_audio_from_video(self, video_path: str, output_audio_path: str) -> Optional[str]:
        """Extract audio from video file."""
        try:
            video = VideoFileClip(video_path)
            
            if video.audio is None:
                logger.error("O vídeo não contém trilha de áudio")
                return None
            
            video.audio.write_audiofile(
                output_audio_path,
                codec='libmp3lame',
                verbose=False,
                logger=None
            )
            
            video.close()
            return output_audio_path
            
        except Exception as e:
            logger.error(f"Erro ao extrair áudio do vídeo: {e}")
            return None
    
    def check_groq_file_size(self, filepath: str) -> bool:
        """Check if file size is within Groq API limits."""
        try:
            file_size = os.path.getsize(filepath)
            return file_size <= GROQ_API_MAX_FILE_SIZE
        except Exception:
            return False
    
    def reduce_audio_segment_size(self, input_audio_path: str, output_audio_path: str) -> bool:
        """Reduce audio quality to fit within size limits."""
        try:
            audio = AudioSegment.from_file(input_audio_path)
            
            # Reduce quality: lower bitrate and sample rate
            audio = audio.set_frame_rate(16000)  # 16kHz
            audio = audio.set_channels(1)  # Mono
            
            # Export with lower bitrate
            audio.export(output_audio_path, format="mp3", bitrate="32k")
            
            return self.check_groq_file_size(output_audio_path)
            
        except Exception as e:
            logger.error(f"Erro ao reduzir qualidade do áudio: {e}")
            return False
    
    def split_audio_into_segments(self, audio_path: str, segment_duration_ms: int = SEGMENT_DURATION_MS) -> List[str]:
        """Split audio file into smaller segments."""
        try:
            audio = AudioSegment.from_file(audio_path)
            segments = []
            
            # Calculate number of segments needed
            total_duration = len(audio)
            num_segments = math.ceil(total_duration / segment_duration_ms)
            
            logger.info(f"Dividindo áudio em {num_segments} segmentos de {segment_duration_ms/1000/60:.1f} minutos")
            
            for i in range(num_segments):
                start_time = i * segment_duration_ms
                end_time = min((i + 1) * segment_duration_ms, total_duration)
                
                segment = audio[start_time:end_time]
                
                # Create temporary file for segment
                with tempfile.NamedTemporaryFile(suffix=f'_segment_{i}.mp3', delete=False) as temp_file:
                    segment_path = temp_file.name
                    segment.export(segment_path, format="mp3", bitrate="64k")
                    
                    # Check if segment is still too large
                    if not self.check_groq_file_size(segment_path):
                        # Try to reduce quality further
                        reduced_path = segment_path.replace('.mp3', '_reduced.mp3')
                        if self.reduce_audio_segment_size(segment_path, reduced_path):
                            os.unlink(segment_path)
                            segment_path = reduced_path
                        else:
                            logger.warning(f"Segmento {i} ainda muito grande após redução")
                    
                    segments.append(segment_path)
            
            return segments
            
        except Exception as e:
            logger.error(f"Erro ao dividir áudio em segmentos: {e}")
            return []
    
    def api_call_with_retry(self, endpoint: str, headers: dict, files: dict, data: dict) -> Optional[dict]:
        """Make API call with retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(endpoint, headers=headers, files=files, data=data, timeout=300)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    wait_time = min(INITIAL_BACKOFF * (2 ** attempt), MAX_BACKOFF)
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {e}")
            
            if attempt < MAX_RETRIES - 1:
                wait_time = min(INITIAL_BACKOFF * (2 ** attempt), MAX_BACKOFF)
                time.sleep(wait_time)
        
        return None
    
    def transcribe_audio_segment(self, segment_path: str, model_id: str, segment_index: int, 
                               segment_start_time: float = 0, include_timestamps: bool = True) -> Optional[str]:
        """Transcribe a single audio segment."""
        try:
            logger.info(f"Transcrevendo segmento {segment_index + 1}")
            
            endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {self.groq_api_key}"}
            
            with open(segment_path, 'rb') as audio_file:
                files = {"file": (os.path.basename(segment_path), audio_file, "audio/mpeg")}
                data = {
                    "model": model_id,
                    "temperature": 0.0,
                    "response_format": "verbose_json" if include_timestamps else "text"
                }
                
                result = self.api_call_with_retry(endpoint, headers, files, data)
                
                if result:
                    if include_timestamps and 'segments' in result:
                        # Format with adjusted timestamps
                        formatted_segments = []
                        for seg in result['segments']:
                            start_time = seg.get('start', 0) + segment_start_time
                            text = seg.get('text', '').strip()
                            if text:
                                timestamp = self.format_timestamp(start_time)
                                formatted_segments.append(f"{timestamp} {text}")
                        return '\n'.join(formatted_segments)
                    else:
                        return result.get('text', '')
                
        except Exception as e:
            logger.error(f"Erro na transcrição do segmento {segment_index}: {e}")
        
        return None
    
    def transcribe_audio_groq(self, audio_path: str, model_id: str, include_timestamps: bool = True) -> Optional[str]:
        """Transcribe audio using Groq API with automatic segmentation for large files."""
        try:
            # Check if file is within size limits
            if self.check_groq_file_size(audio_path):
                logger.info("Arquivo dentro do limite, transcrevendo diretamente")
                return self.transcribe_single_file(audio_path, model_id, include_timestamps)
            
            logger.info("Arquivo muito grande, dividindo em segmentos")
            
            # Split into segments
            segments = self.split_audio_into_segments(audio_path)
            if not segments:
                logger.error("Falha ao dividir arquivo em segmentos")
                return None
            
            # Transcribe each segment
            all_transcriptions = []
            segment_duration_seconds = SEGMENT_DURATION_MS / 1000
            
            for i, segment_path in enumerate(segments):
                try:
                    segment_start_time = i * segment_duration_seconds
                    transcription = self.transcribe_audio_segment(
                        segment_path, model_id, i, segment_start_time, include_timestamps
                    )
                    
                    if transcription:
                        all_transcriptions.append(transcription)
                    else:
                        logger.warning(f"Falha na transcrição do segmento {i + 1}")
                    
                    # Cleanup segment file
                    try:
                        os.unlink(segment_path)
                    except:
                        pass
                        
                except Exception as e:
                    logger.error(f"Erro no segmento {i + 1}: {e}")
                    # Cleanup on error
                    try:
                        os.unlink(segment_path)
                    except:
                        pass
            
            # Combine all transcriptions
            if all_transcriptions:
                final_transcription = '\n'.join(all_transcriptions)
                logger.info(f"Transcrição completa: {len(segments)} segmentos processados")
                return final_transcription
            else:
                logger.error("Nenhum segmento foi transcrito com sucesso")
                return None
                
        except Exception as e:
            logger.error(f"Erro na transcrição Groq: {e}")
            return None
    
    def transcribe_single_file(self, audio_path: str, model_id: str, include_timestamps: bool = True) -> Optional[str]:
        """Transcribe a single audio file (within size limits)."""
        try:
            endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {self.groq_api_key}"}
            
            with open(audio_path, 'rb') as audio_file:
                files = {"file": (os.path.basename(audio_path), audio_file, "audio/mpeg")}
                data = {
                    "model": model_id,
                    "temperature": 0.0,
                    "response_format": "verbose_json" if include_timestamps else "text"
                }
                
                result = self.api_call_with_retry(endpoint, headers, files, data)
                
                if result:
                    if include_timestamps and 'segments' in result:
                        # Format with timestamps
                        formatted_segments = []
                        for segment in result['segments']:
                            start_time = segment.get('start', 0)
                            text = segment.get('text', '').strip()
                            if text:
                                timestamp = self.format_timestamp(start_time)
                                formatted_segments.append(f"{timestamp} {text}")
                        return '\n'.join(formatted_segments)
                    else:
                        return result.get('text', '')
                
        except Exception as e:
            logger.error(f"Erro na transcrição de arquivo único: {e}")
        
        return None


class YouTubeExtractorService:
    """Service for YouTube content extraction."""
    
    def __init__(self):
        self.transcription_service = TranscriptionService()
    
    def extract_transcript(self, transcription: Transcription) -> bool:
        """Extract transcript from YouTube video."""
        try:
            transcription.status = 'processing'
            transcription.save()
            
            transcript_text, title, upload_date, lang, subtitle_type = \
                self.transcription_service.extract_youtube_transcript(transcription.source_url)
            
            if transcript_text:
                transcription.transcription_text = transcript_text
                transcription.title = title
                transcription.language_detected = lang
                transcription.status = 'completed'
                transcription.completed_at = timezone.now()
            else:
                transcription.status = 'failed'
                transcription.error_message = 'Não foi possível extrair legendas do vídeo'
            
            transcription.save()
            return transcription.status == 'completed'
            
        except Exception as e:
            logger.error(f"Erro ao extrair transcrição do YouTube: {e}")
            transcription.status = 'failed'
            transcription.error_message = str(e)
            transcription.save()
            return False


class AudioTranscriptionService:
    """Service for audio/video transcription."""
    
    def __init__(self):
        self.transcription_service = TranscriptionService()
    
    def process_transcription(self, transcription: Transcription) -> bool:
        """Process audio/video transcription with automatic segmentation for large files."""
        try:
            transcription.status = 'processing'
            transcription.save()
            
            # Determine file path
            if transcription.source_type == 'video_upload' and transcription.video_file:
                file_path = transcription.video_file.path
                temp_audio_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                audio_path = self.transcription_service.extract_audio_from_video(
                    file_path, temp_audio_file.name
                )
                temp_audio_file.close() # Close the file handle, but don't delete yet

                if not audio_path:
                    raise Exception("Falha ao extrair áudio do vídeo")
                temp_audio_created = True
            elif transcription.source_type == 'audio_upload' and transcription.audio_file:
                audio_path = transcription.audio_file.path
                temp_audio_created = False
            else:
                raise Exception("Arquivo não encontrado")
            
            # Log file size for debugging
            file_size = os.path.getsize(audio_path)
            logger.info(f"Processando arquivo de {file_size / (1024*1024):.1f} MB")
            
            # Transcribe with automatic segmentation
            transcript_text = self.transcription_service.transcribe_audio_groq(
                audio_path, 
                transcription.model_used or 'whisper-large-v3-turbo',
                transcription.include_timestamps
            )
            
            if transcript_text:
                transcription.transcription_text = transcript_text
                transcription.status = 'completed'
                transcription.completed_at = timezone.now()
                logger.info(f"Transcrição concluída com sucesso: {len(transcript_text)} caracteres")
            else:
                transcription.status = 'failed'
                transcription.error_message = 'Falha na transcrição'
            
            # Cleanup temp file if created
            if temp_audio_created:
                try:
                    os.unlink(audio_path)
                except:
                    pass
            
            transcription.save()
            return transcription.status == 'completed'
            
        except Exception as e:
            logger.error(f"Erro no processamento de transcrição: {e}")
            transcription.status = 'failed'
            transcription.error_message = str(e)
            transcription.save()
            return False 