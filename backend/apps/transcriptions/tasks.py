"""
Celery tasks for transcription processing.
"""
from celery import shared_task
from django.utils import timezone
from .models import Transcription
from .services import YouTubeExtractorService, AudioTranscriptionService
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_youtube_transcription(self, transcription_id):
    """Process YouTube video transcription."""
    try:
        transcription = Transcription.objects.get(id=transcription_id)
        service = YouTubeExtractorService()
        
        success = service.extract_transcript(transcription)
        
        if success:
            return {
                'status': 'success',
                'transcription_id': str(transcription_id),
                'message': 'Transcrição do YouTube concluída com sucesso'
            }
        else:
            return {
                'status': 'failed',
                'transcription_id': str(transcription_id),
                'message': 'Falha na extração da transcrição do YouTube'
            }
            
    except Transcription.DoesNotExist:
        logger.error(f"Transcrição {transcription_id} não encontrada")
        return {
            'status': 'error',
            'message': 'Transcrição não encontrada'
        }
    except Exception as exc:
        logger.error(f"Erro no processamento da transcrição YouTube {transcription_id}: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        
        # Mark as failed after max retries
        try:
            transcription = Transcription.objects.get(id=transcription_id)
            transcription.status = 'failed'
            transcription.error_message = f"Falha após {self.max_retries} tentativas: {str(exc)}"
            transcription.save()
        except:
            pass
        
        return {
            'status': 'error',
            'transcription_id': str(transcription_id),
            'message': f'Erro após {self.max_retries} tentativas: {str(exc)}'
        }


@shared_task(bind=True, max_retries=3)
def process_audio_transcription(self, transcription_id):
    """Process audio/video file transcription."""
    try:
        transcription = Transcription.objects.get(id=transcription_id)
        service = AudioTranscriptionService()
        
        success = service.process_transcription(transcription)
        
        if success:
            return {
                'status': 'success',
                'transcription_id': str(transcription_id),
                'message': 'Transcrição de áudio concluída com sucesso'
            }
        else:
            return {
                'status': 'failed',
                'transcription_id': str(transcription_id),
                'message': 'Falha na transcrição do áudio'
            }
            
    except Transcription.DoesNotExist:
        logger.error(f"Transcrição {transcription_id} não encontrada")
        return {
            'status': 'error',
            'message': 'Transcrição não encontrada'
        }
    except Exception as exc:
        logger.error(f"Erro no processamento da transcrição de áudio {transcription_id}: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        
        # Mark as failed after max retries
        try:
            transcription = Transcription.objects.get(id=transcription_id)
            transcription.status = 'failed'
            transcription.error_message = f"Falha após {self.max_retries} tentativas: {str(exc)}"
            transcription.save()
        except:
            pass
        
        return {
            'status': 'error',
            'transcription_id': str(transcription_id),
            'message': f'Erro após {self.max_retries} tentativas: {str(exc)}'
        } 