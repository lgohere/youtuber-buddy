"""
Serializers for transcription functionality.
"""
from rest_framework import serializers
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from .models import Transcription, TranscriptionSegment
import mimetypes
import os


class TranscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transcriptions."""
    
    class Meta:
        model = Transcription
        fields = [
            'source_type', 'source_url', 'audio_file', 'video_file',
            'include_timestamps', 'model_used'
        ]
        extra_kwargs = {
            'source_url': {'required': False},
            'audio_file': {'required': False},
            'video_file': {'required': False},
        }
    
    def validate(self, data):
        """Validate transcription data."""
        source_type = data.get('source_type')
        
        if source_type == 'youtube':
            if not data.get('source_url'):
                raise serializers.ValidationError("URL do YouTube é obrigatória para este tipo.")
        
        elif source_type == 'audio_upload':
            if not data.get('audio_file'):
                raise serializers.ValidationError("Arquivo de áudio é obrigatório para este tipo.")
            
            # Validate audio file
            audio_file = data.get('audio_file')
            if audio_file:
                self._validate_audio_file(audio_file)
        
        elif source_type == 'video_upload':
            if not data.get('video_file'):
                raise serializers.ValidationError("Arquivo de vídeo é obrigatório para este tipo.")
            
            # Validate video file
            video_file = data.get('video_file')
            if video_file:
                self._validate_video_file(video_file)
        
        return data
    
    def _validate_audio_file(self, file):
        """Validate audio file format and size."""
        # Check file size (500MB limit)
        max_size = 500 * 1024 * 1024  # 500MB
        if file.size > max_size:
            raise serializers.ValidationError(
                f"Arquivo muito grande. Tamanho máximo: 500MB. Seu arquivo: {file.size / (1024*1024):.1f}MB"
            )
        
        # Check file format
        allowed_audio_types = [
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/flac',
            'audio/aac', 'audio/ogg', 'audio/m4a', 'audio/x-m4a'
        ]
        
        content_type = getattr(file, 'content_type', None)
        if content_type and content_type not in allowed_audio_types:
            # Try to guess from filename
            if hasattr(file, 'name'):
                guessed_type, _ = mimetypes.guess_type(file.name)
                if guessed_type not in allowed_audio_types:
                    raise serializers.ValidationError(
                        "Formato de áudio não suportado. Formatos aceitos: MP3, WAV, FLAC, AAC, OGG, M4A"
                    )
    
    def _validate_video_file(self, file):
        """Validate video file format and size."""
        # Check file size (1GB limit)
        max_size = 1024 * 1024 * 1024  # 1GB
        if file.size > max_size:
            raise serializers.ValidationError(
                f"Arquivo muito grande. Tamanho máximo: 1GB. Seu arquivo: {file.size / (1024*1024):.1f}MB"
            )
        
        # Check file format
        allowed_video_types = [
            'video/mp4', 'video/avi', 'video/mov', 'video/mkv',
            'video/wmv', 'video/flv', 'video/webm', 'video/quicktime'
        ]
        
        content_type = getattr(file, 'content_type', None)
        if content_type and content_type not in allowed_video_types:
            # Try to guess from filename
            if hasattr(file, 'name'):
                guessed_type, _ = mimetypes.guess_type(file.name)
                if guessed_type not in allowed_video_types:
                    raise serializers.ValidationError(
                        "Formato de vídeo não suportado. Formatos aceitos: MP4, AVI, MOV, MKV, WMV, FLV, WebM"
                    )
    
    def create(self, validated_data):
        """Create transcription without requiring user."""
        # Only assign user if authenticated
        request_user = self.context['request'].user
        if request_user.is_authenticated:
            validated_data['user'] = request_user
        # If anonymous, user will be None (which is allowed now)
        
        # Set original filename
        if validated_data.get('audio_file'):
            validated_data['original_filename'] = validated_data['audio_file'].name
        elif validated_data.get('video_file'):
            validated_data['original_filename'] = validated_data['video_file'].name
        
        # Set default model if not provided
        if not validated_data.get('model_used'):
            validated_data['model_used'] = 'whisper-large-v3-turbo'
        
        return super().create(validated_data)


class TranscriptionSegmentSerializer(serializers.ModelSerializer):
    """Serializer for transcription segments."""
    
    class Meta:
        model = TranscriptionSegment
        fields = ['segment_number', 'start_time', 'end_time', 'text', 'confidence']


class TranscriptionDetailSerializer(serializers.ModelSerializer):
    """Serializer for transcription details."""
    
    segments = TranscriptionSegmentSerializer(many=True, read_only=True)
    user_email = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Transcription
        fields = [
            'id', 'user_email', 'source_type', 'source_url', 'original_filename',
            'status', 'model_used', 'language_detected', 'title',
            'transcription_text', 'include_timestamps', 'duration_seconds',
            'file_size_mb', 'file_size_display', 'duration_display',
            'processing_time_seconds', 'error_message', 'retry_count',
            'created_at', 'updated_at', 'completed_at', 'segments'
        ]
        read_only_fields = [
            'id', 'user_email', 'status', 'language_detected', 'title',
            'transcription_text', 'duration_seconds', 'file_size_mb',
            'processing_time_seconds', 'error_message', 'retry_count',
            'created_at', 'updated_at', 'completed_at'
        ]
    
    def get_user_email(self, obj):
        """Get user email or return 'Anônimo' if no user."""
        return obj.user.email if obj.user else 'Anônimo'
    
    def get_file_size_display(self, obj):
        """Get human readable file size."""
        if obj.file_size_mb:
            if obj.file_size_mb < 1:
                return f"{obj.file_size_mb * 1024:.1f} KB"
            else:
                return f"{obj.file_size_mb:.1f} MB"
        return None
    
    def get_duration_display(self, obj):
        """Get human readable duration."""
        if obj.duration_seconds:
            hours, remainder = divmod(obj.duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        return None


class TranscriptionListSerializer(serializers.ModelSerializer):
    """Serializer for transcription list."""
    
    file_size_display = serializers.SerializerMethodField()
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Transcription
        fields = [
            'id', 'source_type', 'original_filename', 'title', 'status',
            'language_detected', 'file_size_display', 'duration_display',
            'created_at', 'completed_at'
        ]
    
    def get_file_size_display(self, obj):
        """Get human readable file size."""
        if obj.file_size_mb:
            if obj.file_size_mb < 1:
                return f"{obj.file_size_mb * 1024:.1f} KB"
            else:
                return f"{obj.file_size_mb:.1f} MB"
        return None
    
    def get_duration_display(self, obj):
        """Get human readable duration."""
        if obj.duration_seconds:
            hours, remainder = divmod(obj.duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        return None 