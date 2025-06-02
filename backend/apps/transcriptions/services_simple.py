"""
Simplified transcription service - Direct processing without Celery
Based on the working Streamlit implementation
"""
import os
import re
import time
import json
import random
import logging
import requests
import tempfile
from typing import Optional, Tuple
from django.conf import settings
from django.utils import timezone
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
from .models import Transcription

logger = logging.getLogger(__name__)

# Configurações da API Groq
GROQ_API_MAX_FILE_SIZE = 24 * 1024 * 1024  # 24 MB
MAX_RETRIES = 5
INITIAL_BACKOFF = 2
MAX_BACKOFF = 60
SEGMENT_DURATION_MS = 5 * 60 * 1000  # 5 minutos


class SimpleTranscriptionService:
    """Serviço de transcrição simplificado - processamento direto"""
    
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY não encontrada nas configurações")
    
    def format_timestamp(self, timestamp_float: float) -> str:
        """Formatar timestamp para HH:MM:SS"""
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
    
    def check_groq_file_size(self, filepath: str) -> Tuple[int, bool]:
        """Verificar se o arquivo está dentro do limite da API Groq"""
        file_size = os.path.getsize(filepath)
        return file_size, file_size <= GROQ_API_MAX_FILE_SIZE
    
    def api_call_with_retry(self, endpoint: str, headers: dict, files: dict, data: dict) -> Optional[dict]:
        """Fazer chamada à API com retry e backoff exponencial"""
        retry_count = 0
        backoff = INITIAL_BACKOFF
        
        while retry_count <= MAX_RETRIES:
            try:
                logger.info(f"Tentativa {retry_count + 1} de {MAX_RETRIES + 1} para API Groq")
                
                response = requests.post(endpoint, headers=headers, files=files, data=data, timeout=300)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    logger.warning(f"Rate limit atingido, aguardando {backoff}s")
                    time.sleep(backoff)
                else:
                    logger.error(f"Erro da API {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout na tentativa {retry_count + 1}")
            except Exception as e:
                logger.error(f"Erro na tentativa {retry_count + 1}: {e}")
            
            if retry_count < MAX_RETRIES:
                backoff = min(MAX_BACKOFF, backoff * 2 * (1 + random.random() * 0.1))
                time.sleep(backoff)
            
            retry_count += 1
        
        return None
    
    def transcribe_single_file(self, audio_path: str, model_id: str, include_timestamps: bool = True) -> Optional[str]:
        """Transcrever um único arquivo de áudio"""
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
                        # Formatar com timestamps
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
    
    def split_audio_into_segments(self, audio_path: str) -> list:
        """Dividir áudio em segmentos menores"""
        try:
            audio = AudioSegment.from_file(audio_path)
            total_duration_ms = len(audio)
            segments = []
            
            temp_dir = os.path.join(os.path.dirname(audio_path), f"temp_segments_{int(time.time())}")
            os.makedirs(temp_dir, exist_ok=True)
            
            current_pos_ms = 0
            segment_idx = 0
            
            while current_pos_ms < total_duration_ms:
                end_ms = min(current_pos_ms + SEGMENT_DURATION_MS, total_duration_ms)
                segment_audio = audio[current_pos_ms:end_ms]
                
                segment_path = os.path.join(temp_dir, f"segment_{segment_idx:04d}.mp3")
                segment_audio.export(segment_path, format="mp3", bitrate="128k")
                
                # Verificar tamanho e reduzir se necessário
                file_size, is_within_limit = self.check_groq_file_size(segment_path)
                
                if not is_within_limit:
                    # Reduzir qualidade
                    segment_audio.export(segment_path, format="mp3", bitrate="64k")
                    file_size, is_within_limit = self.check_groq_file_size(segment_path)
                    
                    if not is_within_limit:
                        segment_audio.export(segment_path, format="mp3", bitrate="32k")
                
                segments.append({
                    'path': segment_path,
                    'start_time_seconds': current_pos_ms / 1000.0,
                    'end_time_seconds': end_ms / 1000.0,
                    'index': segment_idx
                })
                
                current_pos_ms = end_ms
                segment_idx += 1
            
            return segments
            
        except Exception as e:
            logger.error(f"Erro ao dividir áudio em segmentos: {e}")
            return []
    
    def transcribe_audio_segments(self, segments: list, model_id: str, include_timestamps: bool = True) -> Optional[str]:
        """Transcrever múltiplos segmentos de áudio"""
        try:
            all_transcriptions = []
            
            for i, segment_info in enumerate(segments):
                logger.info(f"Transcrevendo segmento {i + 1} de {len(segments)}")
                
                endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"
                headers = {"Authorization": f"Bearer {self.groq_api_key}"}
                
                with open(segment_info['path'], 'rb') as audio_file:
                    files = {"file": (os.path.basename(segment_info['path']), audio_file, "audio/mpeg")}
                    data = {
                        "model": model_id,
                        "temperature": 0.0,
                        "response_format": "verbose_json" if include_timestamps else "text"
                    }
                    
                    result = self.api_call_with_retry(endpoint, headers, files, data)
                    
                    if result:
                        if include_timestamps and 'segments' in result:
                            # Ajustar timestamps baseado no tempo de início do segmento
                            formatted_segments = []
                            for seg in result['segments']:
                                start_time = seg.get('start', 0) + segment_info['start_time_seconds']
                                text = seg.get('text', '').strip()
                                if text:
                                    timestamp = self.format_timestamp(start_time)
                                    formatted_segments.append(f"{timestamp} {text}")
                            all_transcriptions.append('\n'.join(formatted_segments))
                        else:
                            text = result.get('text', '')
                            if include_timestamps and text:
                                timestamp = self.format_timestamp(segment_info['start_time_seconds'])
                                all_transcriptions.append(f"{timestamp} {text}")
                            else:
                                all_transcriptions.append(text)
                    else:
                        logger.warning(f"Falha na transcrição do segmento {i + 1}")
                
                # Limpar arquivo do segmento
                try:
                    os.unlink(segment_info['path'])
                except:
                    pass
                
                # Pausa para não sobrecarregar a API
                time.sleep(1)
            
            # Limpar diretório temporário
            try:
                import shutil
                temp_dir = os.path.dirname(segments[0]['path'])
                shutil.rmtree(temp_dir)
            except:
                pass
            
            return '\n\n'.join(filter(None, all_transcriptions))
            
        except Exception as e:
            logger.error(f"Erro na transcrição de segmentos: {e}")
            return None
    
    def extract_audio_from_video(self, video_path: str, output_audio_path: str) -> Optional[str]:
        """Extrair áudio de arquivo de vídeo"""
        try:
            logger.info(f"Extraindo áudio de: {video_path}")
            video = VideoFileClip(video_path)
            
            if video.audio is None:
                logger.error("O vídeo não contém áudio")
                video.close()
                return None
            
            video.audio.write_audiofile(
                output_audio_path,
                codec='libmp3lame',
                verbose=False,
                logger=None
            )
            
            video.close()
            
            if os.path.exists(output_audio_path) and os.path.getsize(output_audio_path) > 0:
                logger.info(f"Áudio extraído com sucesso: {output_audio_path}")
                return output_audio_path
            else:
                logger.error("Arquivo de áudio não foi criado ou está vazio")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao extrair áudio do vídeo: {e}")
            try:
                if 'video' in locals():
                    video.close()
            except:
                pass
            return None
    
    def process_transcription_direct(self, transcription: Transcription) -> bool:
        """Processar transcrição diretamente - SEM CELERY"""
        try:
            logger.info(f"Iniciando processamento direto da transcrição {transcription.id}")
            
            # Atualizar status
            transcription.status = 'processing'
            transcription.save()
            
            # Determinar arquivo de áudio
            audio_path = None
            temp_audio_path = None
            
            if transcription.source_type == 'audio_upload' and transcription.audio_file:
                audio_path = transcription.audio_file.path
            elif transcription.source_type == 'video_upload' and transcription.video_file:
                # Extrair áudio do vídeo
                temp_audio_path = os.path.join(
                    tempfile.gettempdir(),
                    f"temp_audio_{transcription.id}.mp3"
                )
                audio_path = self.extract_audio_from_video(
                    transcription.video_file.path,
                    temp_audio_path
                )
                if not audio_path:
                    raise Exception("Falha ao extrair áudio do vídeo")
            else:
                raise Exception("Tipo de fonte não suportado ou arquivo não encontrado")
            
            # Verificar tamanho do arquivo
            file_size, is_within_limit = self.check_groq_file_size(audio_path)
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"Processando arquivo de {file_size_mb:.2f} MB")
            
            # Escolher método de transcrição
            model_id = transcription.model_used or "whisper-large-v3-turbo"
            
            if is_within_limit:
                logger.info("Arquivo dentro do limite, transcrevendo diretamente")
                transcription_text = self.transcribe_single_file(
                    audio_path, 
                    model_id, 
                    transcription.include_timestamps
                )
            else:
                logger.info("Arquivo muito grande, dividindo em segmentos")
                segments = self.split_audio_into_segments(audio_path)
                if not segments:
                    raise Exception("Falha ao dividir arquivo em segmentos")
                
                transcription_text = self.transcribe_audio_segments(
                    segments, 
                    model_id, 
                    transcription.include_timestamps
                )
            
            # Salvar resultado
            if transcription_text:
                transcription.transcription_text = transcription_text
                transcription.status = 'completed'
                transcription.completed_at = timezone.now()
                transcription.file_size_mb = file_size_mb
                
                # Calcular duração aproximada (se possível)
                try:
                    audio = AudioSegment.from_file(audio_path)
                    transcription.duration_seconds = len(audio) / 1000
                except:
                    pass
                
                logger.info(f"Transcrição concluída com sucesso para {transcription.id}")
            else:
                raise Exception("Falha na transcrição do áudio")
            
            transcription.save()
            
            # Limpar arquivo temporário
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro no processamento da transcrição {transcription.id}: {e}")
            
            transcription.status = 'failed'
            transcription.error_message = str(e)
            transcription.save()
            
            # Limpar arquivo temporário
            if 'temp_audio_path' in locals() and temp_audio_path and os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            
            return False 