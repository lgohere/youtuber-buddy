"""
Views for content generation functionality.
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import logging

from .models import ContentGeneration
from .serializers import (
    ContentGenerationCreateSerializer,
    ContentGenerationDetailSerializer,
    ContentGenerationListSerializer
)
from .tasks import process_content_generation
from apps.transcriptions.models import Transcription
from apps.transcriptions.serializers import TranscriptionListSerializer

logger = logging.getLogger(__name__)


class ContentGenerationCreateView(generics.CreateAPIView):
    """Create new content generation."""
    
    serializer_class = ContentGenerationCreateSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Override create to handle errors properly."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Save content generation
            content_generation = serializer.save()
            
            # Start processing task
            task = process_content_generation.delay(str(content_generation.id))
            logger.info(f"Started content generation task {task.id} for {content_generation.id}")
            
            # Return detailed response
            response_serializer = ContentGenerationDetailSerializer(content_generation)
            
            return Response(
                {
                    'message': 'Geração de conteúdo criada com sucesso. Processamento iniciado.',
                    'content_generation': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating content generation: {e}")
            return Response(
                {'error': f'Erro ao criar geração de conteúdo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContentGenerationListView(generics.ListAPIView):
    """List user content generations."""
    
    serializer_class = ContentGenerationListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'content_type', 'language_detected']
    search_fields = ['transcription__title', 'transcription__original_filename']
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get all content generations."""
        return ContentGeneration.objects.all()


class ContentGenerationDetailView(generics.RetrieveAPIView):
    """Get content generation details."""
    
    serializer_class = ContentGenerationDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Get all content generations."""
        return ContentGeneration.objects.all()


class ContentGenerationDeleteView(generics.DestroyAPIView):
    """Delete content generation."""
    
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Get all content generations."""
        return ContentGeneration.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        """Delete content generation with custom response."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Geração de conteúdo deletada com sucesso'},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def content_generation_status_view(request, content_generation_id):
    """Get content generation status."""
    try:
        content_generation = get_object_or_404(
            ContentGeneration,
            id=content_generation_id
        )
        
        serializer = ContentGenerationDetailSerializer(content_generation)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting content generation status: {e}")
        return Response(
            {'error': 'Erro ao buscar status da geração de conteúdo'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def retry_content_generation_view(request, content_generation_id):
    """Retry failed content generation."""
    try:
        content_generation = get_object_or_404(
            ContentGeneration,
            id=content_generation_id
        )
        
        if content_generation.status != 'failed':
            return Response(
                {'error': 'Apenas gerações de conteúdo com falha podem ser reprocessadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset status
        content_generation.status = 'pending'
        content_generation.error_message = None
        content_generation.save()
        
        # Start processing task
        task = process_content_generation.delay(str(content_generation.id))
        logger.info(f"Started content generation retry task {task.id} for {content_generation.id}")
        
        serializer = ContentGenerationDetailSerializer(content_generation)
        return Response({
            'message': 'Geração de conteúdo reiniciada com sucesso',
            'content_generation': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error retrying content generation: {e}")
        return Response(
            {'error': 'Erro ao tentar reprocessar geração de conteúdo'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def user_content_generation_stats_view(request):
    """Get content generation statistics."""
    try:
        content_generations = ContentGeneration.objects.all()
        
        stats = {
            'total_content_generations': content_generations.count(),
            'completed_content_generations': content_generations.filter(status='completed').count(),
            'processing_content_generations': content_generations.filter(status='processing').count(),
            'failed_content_generations': content_generations.filter(status='failed').count(),
            'pending_content_generations': content_generations.filter(status='pending').count(),
        }
        
        return Response(stats)
        
    except Exception as e:
        logger.error(f"Error getting content generation stats: {e}")
        return Response(
            {'error': 'Erro ao buscar estatísticas de geração de conteúdo'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def available_transcriptions_view(request):
    """Get available transcriptions for content generation."""
    try:
        # Get completed transcriptions
        transcriptions = Transcription.objects.filter(
            status='completed'
        ).exclude(
            transcription_text__isnull=True
        ).exclude(
            transcription_text__exact=''
        ).order_by('-created_at')
        
        serializer = TranscriptionListSerializer(transcriptions, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting available transcriptions: {e}")
        return Response(
            {'error': 'Erro ao buscar transcrições disponíveis'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 