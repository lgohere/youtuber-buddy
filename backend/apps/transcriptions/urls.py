"""
URLs for transcription functionality.
"""
from django.urls import path
from . import views

app_name = 'transcriptions'

urlpatterns = [
    # Transcription CRUD
    path('', views.TranscriptionListView.as_view(), name='transcription-list'),
    path('create/', views.TranscriptionCreateView.as_view(), name='transcription-create'),
    path('<uuid:id>/', views.TranscriptionDetailView.as_view(), name='transcription-detail'),
    path('<uuid:id>/delete/', views.TranscriptionDeleteView.as_view(), name='transcription-delete'),
    
    # Transcription status and actions
    path('<uuid:transcription_id>/status/', views.transcription_status_view, name='transcription-status'),
    path('<uuid:transcription_id>/retry/', views.retry_transcription_view, name='transcription-retry'),
    
    # Bulk operations
    path('delete-pending/', views.delete_pending_transcriptions_view, name='delete-pending-transcriptions'),
    
    # User stats
    path('stats/', views.user_transcription_stats_view, name='transcription-stats'),
] 