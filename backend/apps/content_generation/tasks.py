"""
Celery tasks for content generation.
"""
from celery import shared_task
from django.utils import timezone
import logging

from apps.transcriptions.models import Transcription
from .models import ContentGeneration, GeneratedTitle, GeneratedChapter
from .services import ContentGenerationService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_content_generation(self, content_generation_id):
    """
    Process content generation request.
    This task will call the ContentGenerationService to generate content.
    """
    try:
        content_generation = ContentGeneration.objects.get(id=content_generation_id)
        service = ContentGenerationService()
        
        success = service.process_content_generation(content_generation)
        
        if success:
            logger.info(f"Content generation {content_generation_id} completed successfully.")
            return {
                'status': 'success',
                'content_generation_id': str(content_generation_id),
                'message': 'Geração de conteúdo concluída com sucesso'
            }
        else:
            logger.error(f"Content generation {content_generation_id} failed: {content_generation.error_message}")
            return {
                'status': 'failed',
                'content_generation_id': str(content_generation_id),
                'message': f'Falha na geração de conteúdo: {content_generation.error_message}'
            }
            
    except ContentGeneration.DoesNotExist:
        logger.error(f"Content generation {content_generation_id} not found.")
        return {
            'status': 'error',
            'message': 'Geração de conteúdo não encontrada'
        }
    except Exception as exc:
        logger.error(f"Erro no processamento da geração de conteúdo {content_generation_id}: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.warning(f"Retrying content generation task {content_generation_id}. Attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        
        # Mark as failed after max retries
        try:
            content_generation = ContentGeneration.objects.get(id=content_generation_id)
            content_generation.status = 'failed'
            content_generation.error_message = f"Falha após {self.max_retries} tentativas: {str(exc)}"
            content_generation.completed_at = timezone.now()
            content_generation.save()
        except ContentGeneration.DoesNotExist:
            logger.error(f"Content generation {content_generation_id} not found during final error handling.")
        except Exception as inner_exc:
            logger.error(f"Erro ao salvar status de falha para geração de conteúdo {content_generation_id}: {inner_exc}")
        
        return {
            'status': 'error',
            'content_generation_id': str(content_generation_id),
            'message': f'Erro após {self.max_retries} tentativas: {str(exc)}'
        } 