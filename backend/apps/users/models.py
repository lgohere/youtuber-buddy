"""
User models for the application.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with additional fields."""
    
    PLAN_CHOICES = [
        ('free', 'Gratuito'),
        ('premium', 'Premium'),
    ]
    
    email = models.EmailField(unique=True)
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default='free')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Usage tracking
    monthly_transcriptions = models.IntegerField(default=0)
    monthly_content_generations = models.IntegerField(default=0)
    last_reset_date = models.DateField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
    
    def __str__(self):
        return self.email
    
    @property
    def is_premium(self):
        return self.plan == 'premium'
    
    def can_transcribe(self):
        """Check if user can perform transcription based on plan limits."""
        if self.is_premium:
            return True
        return self.monthly_transcriptions < 10  # Free plan limit
    
    def can_generate_content(self):
        """Check if user can generate content based on plan limits."""
        if self.is_premium:
            return True
        return self.monthly_content_generations < 5  # Free plan limit 