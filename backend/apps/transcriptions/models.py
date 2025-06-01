"""
Models for transcription functionality.
"""
from django.db import models
from django.conf import settings
import uuid


class Transcription(models.Model):
    """Model for storing transcription data."""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]
    
    SOURCE_CHOICES = [
        ('youtube', 'YouTube'),
        ('audio_upload', 'Upload de Áudio'),
        ('video_upload', 'Upload de Vídeo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transcriptions', blank=True, null=True)
    
    # Source information
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_url = models.URLField(blank=True, null=True)  # For YouTube videos
    original_filename = models.CharField(max_length=255, blank=True, null=True)  # For uploads
    
    # File handling
    audio_file = models.FileField(upload_to='transcriptions/audio/', blank=True, null=True)
    video_file = models.FileField(upload_to='transcriptions/video/', blank=True, null=True)
    
    # Processing information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    model_used = models.CharField(max_length=50, blank=True, null=True)  # Whisper model
    language_detected = models.CharField(max_length=10, blank=True, null=True)
    
    # Results
    title = models.CharField(max_length=500, blank=True, null=True)
    transcription_text = models.TextField(blank=True, null=True)
    include_timestamps = models.BooleanField(default=True)
    
    # Metadata
    duration_seconds = models.IntegerField(blank=True, null=True)
    file_size_mb = models.FloatField(blank=True, null=True)
    processing_time_seconds = models.FloatField(blank=True, null=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'transcriptions'
        verbose_name = 'Transcrição'
        verbose_name_plural = 'Transcrições'
        ordering = ['-created_at']
    
    def __str__(self):
        user_info = self.user.email if self.user else 'Anônimo'
        return f"{self.title or self.original_filename or 'Transcrição'} - {user_info}"
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_processing(self):
        return self.status == 'processing'
    
    @property
    def has_failed(self):
        return self.status == 'failed'


class TranscriptionSegment(models.Model):
    """Model for storing transcription segments (for large files)."""
    
    transcription = models.ForeignKey(Transcription, on_delete=models.CASCADE, related_name='segments')
    segment_number = models.IntegerField()
    start_time = models.FloatField()  # In seconds
    end_time = models.FloatField()  # In seconds
    text = models.TextField()
    confidence = models.FloatField(blank=True, null=True)
    
    class Meta:
        db_table = 'transcription_segments'
        verbose_name = 'Segmento de Transcrição'
        verbose_name_plural = 'Segmentos de Transcrição'
        ordering = ['transcription', 'segment_number']
        unique_together = ['transcription', 'segment_number']
    
    def __str__(self):
        return f"Segmento {self.segment_number} - {self.transcription}" 