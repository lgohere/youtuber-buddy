"""
Views for transcription functionality.
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Transcription
from .serializers import (
    TranscriptionCreateSerializer,
    TranscriptionDetailSerializer,
    TranscriptionListSerializer
)
from .tasks import process_youtube_transcription, process_audio_transcription

logger = logging.getLogger(__name__)


class TranscriptionCreateView(generics.CreateAPIView):
    """Create new transcription."""
    
    serializer_class = TranscriptionCreateSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def perform_create(self, serializer):
        """Create transcription and start processing."""
        # Save transcription without user
        transcription = serializer.save()
        
        # Calculate file size
        if transcription.audio_file:
            transcription.file_size_mb = transcription.audio_file.size / (1024 * 1024)
        elif transcription.video_file:
            transcription.file_size_mb = transcription.video_file.size / (1024 * 1024)
        
        transcription.save()
        
        # Start processing task
        try:
            if transcription.source_type == 'youtube':
                task = process_youtube_transcription.delay(str(transcription.id))
                logger.info(f"Started YouTube transcription task {task.id} for {transcription.id}")
            else:
                task = process_audio_transcription.delay(str(transcription.id))
                logger.info(f"Started audio transcription task {task.id} for {transcription.id}")
        except Exception as e:
            logger.error(f"Failed to start transcription task: {e}")
            transcription.status = 'failed'
            transcription.error_message = f"Erro ao iniciar processamento: {str(e)}"
            transcription.save()
    
    def create(self, request, *args, **kwargs):
        """Override create to handle errors properly."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            
            # Return detailed response
            transcription = serializer.instance
            response_serializer = TranscriptionDetailSerializer(transcription)
            
            return Response(
                {
                    'message': 'Transcrição criada com sucesso. Processamento iniciado.',
                    'transcription': response_serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except Exception as e:
            logger.error(f"Error creating transcription: {e}")
            return Response(
                {'error': f'Erro ao criar transcrição: {str(e)}'},
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
        """Get all transcriptions."""
        return Transcription.objects.all()


class TranscriptionDetailView(generics.RetrieveAPIView):
    """Get transcription details."""
    
    serializer_class = TranscriptionDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Get all transcriptions."""
        return Transcription.objects.all()


class TranscriptionDeleteView(generics.DestroyAPIView):
    """Delete transcription."""
    
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Get all transcriptions."""
        return Transcription.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        """Delete transcription with custom response."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Transcrição deletada com sucesso'},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def transcription_status_view(request, transcription_id):
    """Get transcription status."""
    try:
        transcription = get_object_or_404(
            Transcription,
            id=transcription_id
        )
        
        serializer = TranscriptionDetailSerializer(transcription)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting transcription status: {e}")
        return Response(
            {'error': 'Erro ao buscar status da transcrição'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def retry_transcription_view(request, transcription_id):
    """Retry failed transcription."""
    try:
        transcription = get_object_or_404(
            Transcription,
            id=transcription_id
        )
        
        if transcription.status != 'failed':
            return Response(
                {'error': 'Apenas transcrições com falha podem ser reprocessadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset status
        transcription.status = 'pending'
        transcription.error_message = None
        transcription.retry_count += 1
        transcription.save()
        
        # Start processing task
        if transcription.source_type == 'youtube':
            task = process_youtube_transcription.delay(str(transcription.id))
        else:
            task = process_audio_transcription.delay(str(transcription.id))
        
        logger.info(f"Retrying transcription {transcription.id}, task {task.id}")
        
        return Response({
            'message': 'Reprocessamento iniciado com sucesso',
            'transcription_id': str(transcription.id),
            'retry_count': transcription.retry_count
        })
        
    except Exception as e:
        logger.error(f"Error retrying transcription: {e}")
        return Response(
            {'error': 'Erro ao reprocessar transcrição'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def delete_pending_transcriptions_view(request):
    """Delete pending transcriptions with filtering options."""
    try:
        # Get filter parameters
        source_type = request.data.get('source_type')
        older_than_hours = request.data.get('older_than_hours')
        limit = request.data.get('limit')
        force = request.data.get('force', False)
        
        # Build query
        queryset = Transcription.objects.filter(status='pending')
        
        if source_type:
            if source_type not in ['youtube', 'audio_upload', 'video_upload']:
                return Response(
                    {'error': 'Tipo de fonte inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = queryset.filter(source_type=source_type)
        
        if older_than_hours:
            try:
                older_than_hours = int(older_than_hours)
                cutoff_time = timezone.now() - timedelta(hours=older_than_hours)
                queryset = queryset.filter(created_at__lt=cutoff_time)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Valor inválido para older_than_hours'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        queryset = queryset.order_by('created_at')
        
        if limit:
            try:
                limit = int(limit)
                queryset = queryset[:limit]
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Valor inválido para limit'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        pending_transcriptions = list(queryset)
        
        if not pending_transcriptions:
            return Response({
                'message': 'Nenhuma transcrição pendente encontrada com os critérios especificados',
                'deleted_count': 0
            })

        # Return preview if not forced
        if not force:
            preview_data = []
            for transcription in pending_transcriptions[:10]:  # Show first 10
                age_hours = (timezone.now() - transcription.created_at).total_seconds() / 3600
                preview_data.append({
                    'id': str(transcription.id),
                    'source_type': transcription.source_type,
                    'filename': transcription.original_filename or transcription.source_url,
                    'age_hours': round(age_hours, 1),
                    'created_at': transcription.created_at
                })
            
            return Response({
                'message': f'Encontradas {len(pending_transcriptions)} transcrições pendentes para deletar',
                'total_count': len(pending_transcriptions),
                'preview': preview_data,
                'requires_confirmation': True
            })

        # Delete transcriptions
        deleted_count = 0
        failed_count = 0
        errors = []
        
        for transcription in pending_transcriptions:
            try:
                transcription.delete()
                deleted_count += 1
            except Exception as e:
                failed_count += 1
                errors.append({
                    'id': str(transcription.id),
                    'error': str(e)
                })

        return Response({
            'message': f'{deleted_count} transcrições deletadas com sucesso',
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'errors': errors if errors else None
        })
        
    except Exception as e:
        logger.error(f"Error deleting pending transcriptions: {e}")
        return Response(
            {'error': 'Erro ao deletar transcrições pendentes'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def user_transcription_stats_view(request):
    """Get transcription statistics."""
    try:
        transcriptions = Transcription.objects.all()
        
        stats = {
            'total_transcriptions': transcriptions.count(),
            'completed_transcriptions': transcriptions.filter(status='completed').count(),
            'processing_transcriptions': transcriptions.filter(status='processing').count(),
            'failed_transcriptions': transcriptions.filter(status='failed').count(),
            'pending_transcriptions': transcriptions.filter(status='pending').count(),
        }
        
        return Response(stats)
        
    except Exception as e:
        logger.error(f"Error getting transcription stats: {e}")
        return Response(
            {'error': 'Erro ao buscar estatísticas'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 