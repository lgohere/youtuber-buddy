"""
Models for content generation functionality.
"""
from django.db import models
from django.conf import settings
import uuid


class ContentGeneration(models.Model):
    """Model for storing content generation requests and results."""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('titles', 'Títulos'),
        ('description', 'Descrição'),
        ('chapters', 'Capítulos'),
        ('complete', 'Pacote Completo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='content_generations', blank=True, null=True)
    transcription = models.ForeignKey('transcriptions.Transcription', on_delete=models.CASCADE, related_name='content_generations')
    
    # Request information
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    use_markdown = models.BooleanField(default=False)
    
    # Type-specific options
    title_types = models.JSONField(default=list, blank=True)  # For titles
    description_type = models.CharField(max_length=50, blank=True, null=True)  # For descriptions
    max_chapters = models.IntegerField(default=6, blank=True, null=True)  # For chapters
    
    # Processing information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    language_detected = models.CharField(max_length=10, blank=True, null=True)
    
    # Results
    generated_content = models.TextField(blank=True, null=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'content_generations'
        verbose_name = 'Geração de Conteúdo'
        verbose_name_plural = 'Gerações de Conteúdo'
        ordering = ['-created_at']
    
    def __str__(self):
        user_info = self.user.email if self.user else 'Anônimo'
        return f"{self.get_content_type_display()} - {self.transcription.title or 'Transcrição'} - {user_info}"
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_processing(self):
        return self.status == 'processing'
    
    @property
    def has_failed(self):
        return self.status == 'failed'


class GeneratedTitle(models.Model):
    """Model for storing individual generated titles."""
    
    content_generation = models.ForeignKey(ContentGeneration, on_delete=models.CASCADE, related_name='titles')
    title_type = models.CharField(max_length=50)
    title_text = models.CharField(max_length=500)
    justification = models.TextField(blank=True, null=True)
    keywords = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'generated_titles'
        verbose_name = 'Título Gerado'
        verbose_name_plural = 'Títulos Gerados'
    
    def __str__(self):
        return f"{self.title_type}: {self.title_text[:50]}..."


class GeneratedChapter(models.Model):
    """Model for storing individual generated chapters."""
    
    content_generation = models.ForeignKey(ContentGeneration, on_delete=models.CASCADE, related_name='chapters')
    chapter_number = models.IntegerField()
    timestamp = models.CharField(max_length=20)  # HH:MM:SS format
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'generated_chapters'
        verbose_name = 'Capítulo Gerado'
        verbose_name_plural = 'Capítulos Gerados'
        ordering = ['content_generation', 'chapter_number']
    
    def __str__(self):
        return f"Cap. {self.chapter_number}: {self.title}" 