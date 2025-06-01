"""
Serializers for content generation functionality.
"""
from rest_framework import serializers
from .models import ContentGeneration, GeneratedTitle, GeneratedChapter
from apps.transcriptions.models import Transcription


class ContentGenerationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating content generation requests."""
    
    transcription_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = ContentGeneration
        fields = [
            'transcription_id', 'content_type', 'use_markdown',
            'title_types', 'description_type', 'max_chapters'
        ]
        extra_kwargs = {
            'title_types': {'required': False},
            'description_type': {'required': False},
            'max_chapters': {'required': False},
        }
    
    def validate_transcription_id(self, value):
        """Validate transcription exists and is completed."""
        try:
            transcription = Transcription.objects.get(id=value)
            if transcription.status != 'completed':
                raise serializers.ValidationError(
                    "A transcrição deve estar concluída para gerar conteúdo"
                )
            return value
        except Transcription.DoesNotExist:
            raise serializers.ValidationError("Transcrição não encontrada")
    
    def validate(self, data):
        """Validate content generation data."""
        content_type = data.get('content_type')
        
        if content_type == 'titles':
            if not data.get('title_types'):
                data['title_types'] = ['clickbait', 'seo', 'descritivo']
        
        elif content_type == 'description':
            if not data.get('description_type'):
                data['description_type'] = 'analítica'
        
        elif content_type == 'chapters':
            if not data.get('max_chapters'):
                data['max_chapters'] = 6
        
        return data
    
    def create(self, validated_data):
        """Create content generation with transcription."""
        transcription_id = validated_data.pop('transcription_id')
        transcription = Transcription.objects.get(id=transcription_id)
        
        # Only assign user if authenticated
        request_user = self.context['request'].user
        if request_user.is_authenticated:
            validated_data['user'] = request_user
        
        validated_data['transcription'] = transcription
        
        return super().create(validated_data)


class GeneratedTitleSerializer(serializers.ModelSerializer):
    """Serializer for generated titles."""
    
    class Meta:
        model = GeneratedTitle
        fields = ['title_type', 'title_text', 'justification', 'keywords']


class GeneratedChapterSerializer(serializers.ModelSerializer):
    """Serializer for generated chapters."""
    
    class Meta:
        model = GeneratedChapter
        fields = ['chapter_number', 'timestamp', 'title', 'description']


class ContentGenerationDetailSerializer(serializers.ModelSerializer):
    """Serializer for content generation details."""
    
    titles = GeneratedTitleSerializer(many=True, read_only=True)
    chapters = GeneratedChapterSerializer(many=True, read_only=True)
    user_email = serializers.SerializerMethodField()
    transcription_title = serializers.CharField(source='transcription.title', read_only=True)
    transcription_filename = serializers.CharField(source='transcription.original_filename', read_only=True)
    
    class Meta:
        model = ContentGeneration
        fields = [
            'id', 'user_email', 'transcription_title', 'transcription_filename',
            'content_type', 'use_markdown', 'title_types', 'description_type',
            'max_chapters', 'status', 'language_detected', 'generated_content',
            'error_message', 'created_at', 'updated_at', 'completed_at',
            'titles', 'chapters'
        ]
        read_only_fields = [
            'id', 'user_email', 'transcription_title', 'transcription_filename',
            'status', 'language_detected', 'generated_content', 'error_message',
            'created_at', 'updated_at', 'completed_at'
        ]

    def get_user_email(self, obj):
        """Get user email or return 'Anônimo' if no user."""
        return obj.user.email if obj.user else 'Anônimo'


class ContentGenerationListSerializer(serializers.ModelSerializer):
    """Serializer for content generation list."""
    
    transcription_title = serializers.CharField(source='transcription.title', read_only=True)
    transcription_filename = serializers.CharField(source='transcription.original_filename', read_only=True)
    
    class Meta:
        model = ContentGeneration
        fields = [
            'id', 'transcription_title', 'transcription_filename',
            'content_type', 'status', 'language_detected',
            'created_at', 'completed_at'
        ] 