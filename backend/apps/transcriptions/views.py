"""
Views for transcription functionality - Direct processing without Celery
"""
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Transcription
from .serializers import (
    TranscriptionCreateSerializer,
    TranscriptionDetailSerializer,
    TranscriptionListSerializer
)
from .services_simple import SimpleTranscriptionService

logger = logging.getLogger(__name__)


class TranscriptionCreateView(generics.CreateAPIView):
    """Create new transcription with direct processing."""
    
    serializer_class = TranscriptionCreateSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        """Create transcription and process directly."""
        # Set user if authenticated
        if self.request.user.is_authenticated:
            serializer.validated_data['user'] = self.request.user
        
        # Save transcription
        transcription = serializer.save()
        
        # Process directly based on source type
        try:
            if transcription.source_type in ['audio_upload', 'video_upload']:
                # Use direct processing service
                service = SimpleTranscriptionService()
                success = service.process_transcription_direct(transcription)
                
                if not success:
                    logger.error(f"Falha no processamento direto da transcrição {transcription.id}")
            
            elif transcription.source_type == 'youtube':
                # For YouTube, we can still use the existing service
                from .services import YouTubeExtractorService
                youtube_service = YouTubeExtractorService()
                success = youtube_service.extract_transcript(transcription)
                
                if not success:
                    logger.error(f"Falha na extração do YouTube para transcrição {transcription.id}")
            
        except Exception as e:
            logger.error(f"Erro no processamento da transcrição {transcription.id}: {e}")
            transcription.status = 'failed'
            transcription.error_message = str(e)
            transcription.save()

    def create(self, request, *args, **kwargs):
        """Create transcription with enhanced response."""
        try:
            response = super().create(request, *args, **kwargs)
            
            if response.status_code == status.HTTP_201_CREATED:
                transcription_id = response.data.get('id')
                logger.info(f"Transcrição criada e processamento iniciado: {transcription_id}")
                
                # Add processing info to response
                response.data['message'] = 'Transcrição criada e processamento iniciado'
                response.data['processing_type'] = 'direct'  # Indicate direct processing
            
            return response
            
        except Exception as e:
            logger.error(f"Erro na criação da transcrição: {e}")
            return Response(
                {'error': 'Erro interno do servidor', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TranscriptionListView(generics.ListAPIView):
    """List user transcriptions."""
    
    serializer_class = TranscriptionListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'source_type', 'language_detected']
    search_fields = ['title', 'original_filename']
    ordering_fields = ['created_at', 'completed_at', 'file_size_mb', 'duration_seconds']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get transcriptions for current user or all if no user."""
        return Transcription.objects.all()


class TranscriptionDetailView(generics.RetrieveAPIView):
    """Get transcription details."""
    
    serializer_class = TranscriptionDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        """Get transcriptions for current user or all if no user."""
        return Transcription.objects.all()


class TranscriptionDeleteView(generics.DestroyAPIView):
    """Delete transcription."""
    
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        """Get transcriptions for current user or all if no user."""
        return Transcription.objects.all()

    def destroy(self, request, *args, **kwargs):
        """Delete transcription with cleanup."""
        transcription = self.get_object()
        transcription_id = transcription.id
        transcription.delete()
        logger.info(f"Transcrição {transcription_id} deletada")
        return Response({'message': 'Transcrição deletada com sucesso'})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def transcription_status_view(request, transcription_id):
    """Get transcription status."""
    try:
        transcription = get_object_or_404(Transcription, id=transcription_id)
        
        return JsonResponse({
            'id': str(transcription.id),
            'status': transcription.status,
            'progress': 100 if transcription.status == 'completed' else (50 if transcription.status == 'processing' else 0),
            'message': transcription.error_message if transcription.status == 'failed' else None,
            'completed_at': transcription.completed_at.isoformat() if transcription.completed_at else None,
            'processing_type': 'direct'  # Indicate direct processing
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status da transcrição {transcription_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def retry_transcription_view(request, transcription_id):
    """Retry failed transcription with direct processing."""
    try:
        transcription = get_object_or_404(Transcription, id=transcription_id)
        
        if transcription.status not in ['failed']:
            return JsonResponse({
                'error': 'Transcrição deve estar com status "failed" para ser reprocessada'
            }, status=400)
        
        # Reset transcription
        transcription.status = 'pending'
        transcription.error_message = None
        transcription.transcription_text = None
        transcription.completed_at = None
        transcription.retry_count += 1
        transcription.save()
        
        # Process directly
        try:
            if transcription.source_type in ['audio_upload', 'video_upload']:
                service = SimpleTranscriptionService()
                success = service.process_transcription_direct(transcription)
                
                if success:
                    logger.info(f"Reprocessamento direto bem-sucedido para {transcription_id}")
                    return JsonResponse({
                        'message': 'Transcrição reprocessada com sucesso',
                        'status': transcription.status,
                        'processing_type': 'direct'
                    })
                else:
                    return JsonResponse({
                        'error': 'Falha no reprocessamento da transcrição'
                    }, status=500)
            
            elif transcription.source_type == 'youtube':
                from .services import YouTubeExtractorService
                youtube_service = YouTubeExtractorService()
                success = youtube_service.extract_transcript(transcription)
                
                if success:
                    logger.info(f"Reprocessamento YouTube bem-sucedido para {transcription_id}")
                    return JsonResponse({
                        'message': 'Transcrição YouTube reprocessada com sucesso',
                        'status': transcription.status,
                        'processing_type': 'direct'
                    })
                else:
                    return JsonResponse({
                        'error': 'Falha no reprocessamento da transcrição YouTube'
                    }, status=500)
            
        except Exception as e:
            logger.error(f"Erro no reprocessamento da transcrição {transcription_id}: {e}")
            transcription.status = 'failed'
            transcription.error_message = str(e)
            transcription.save()
            
            return JsonResponse({
                'error': f'Erro no reprocessamento: {str(e)}'
            }, status=500)
        
    except Exception as e:
        logger.error(f"Erro ao reprocessar transcrição {transcription_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def delete_pending_transcriptions_view(request):
    """Delete pending transcriptions with various filtering options."""
    try:
        # Get filter parameters
        older_than_hours = request.data.get('older_than_hours', 24)
        source_types = request.data.get('source_types', [])
        confirm = request.data.get('confirm', False)
        
        if not confirm:
            return JsonResponse({
                'error': 'Confirmação necessária. Envie "confirm": true'
            }, status=400)
        
        # Build query
        query = Q(status='pending')
        
        # Filter by age
        if older_than_hours:
            cutoff_time = timezone.now() - timezone.timedelta(hours=older_than_hours)
            query &= Q(created_at__lt=cutoff_time)
        
        # Filter by source types
        if source_types:
            query &= Q(source_type__in=source_types)
        
        # Get transcriptions to delete
        transcriptions_to_delete = Transcription.objects.filter(query)
        count = transcriptions_to_delete.count()
        
        if count == 0:
            return JsonResponse({
                'message': 'Nenhuma transcrição pendente encontrada com os critérios especificados',
                'deleted_count': 0
            })
        
        # Delete transcriptions
        deleted_info = []
        for transcription in transcriptions_to_delete:
            deleted_info.append({
                'id': str(transcription.id),
                'source_type': transcription.source_type,
                'created_at': transcription.created_at.isoformat(),
                'original_filename': transcription.original_filename
            })
        
        transcriptions_to_delete.delete()
        
        logger.info(f"Deletadas {count} transcrições pendentes")
        
        return JsonResponse({
            'message': f'{count} transcrições pendentes deletadas com sucesso',
            'deleted_count': count,
            'deleted_transcriptions': deleted_info
        })
        
    except Exception as e:
        logger.error(f"Erro ao deletar transcrições pendentes: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def user_transcription_stats_view(request):
    """Get user transcription statistics."""
    try:
        # Get all transcriptions
        transcriptions = Transcription.objects.all()
        
        # Basic counts
        total_count = transcriptions.count()
        completed_count = transcriptions.filter(status='completed').count()
        processing_count = transcriptions.filter(status='processing').count()
        failed_count = transcriptions.filter(status='failed').count()
        pending_count = transcriptions.filter(status='pending').count()
        
        # Source type breakdown
        source_stats = transcriptions.values('source_type').annotate(
            count=Count('id')
        ).order_by('source_type')
        
        # Calculate averages for completed transcriptions
        completed_transcriptions = transcriptions.filter(status='completed')
        avg_duration = completed_transcriptions.aggregate(
            avg_duration=Avg('duration_seconds')
        )['avg_duration'] or 0
        
        avg_file_size = completed_transcriptions.aggregate(
            avg_size=Avg('file_size_mb')
        )['avg_size'] or 0
        
        total_duration = completed_transcriptions.aggregate(
            total_duration=Sum('duration_seconds')
        )['total_duration'] or 0
        
        # Recent activity (last 7 days)
        recent_cutoff = timezone.now() - timezone.timedelta(days=7)
        recent_count = transcriptions.filter(created_at__gte=recent_cutoff).count()
        
        return JsonResponse({
            'total_transcriptions': total_count,
            'status_breakdown': {
                'completed': completed_count,
                'processing': processing_count,
                'failed': failed_count,
                'pending': pending_count
            },
            'source_type_breakdown': list(source_stats),
            'averages': {
                'duration_seconds': round(avg_duration, 2),
                'file_size_mb': round(avg_file_size, 2)
            },
            'totals': {
                'duration_seconds': total_duration,
                'duration_formatted': f"{int(total_duration // 3600):02d}:{int((total_duration % 3600) // 60):02d}:{int(total_duration % 60):02d}"
            },
            'recent_activity': {
                'last_7_days': recent_count
            },
            'processing_type': 'direct'  # Indicate direct processing
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de transcrições: {e}")
        return JsonResponse({'error': str(e)}, status=500) 