"""
URLs for content generation functionality.
"""
from django.urls import path
from . import views

app_name = 'content_generation'

urlpatterns = [
    # Content Generation CRUD
    path('', views.ContentGenerationListView.as_view(), name='content-generation-list'),
    path('create/', views.ContentGenerationCreateView.as_view(), name='content-generation-create'),
    path('<uuid:id>/', views.ContentGenerationDetailView.as_view(), name='content-generation-detail'),
    path('<uuid:id>/delete/', views.ContentGenerationDeleteView.as_view(), name='content-generation-delete'),
    
    # Content Generation status and actions
    path('<uuid:content_generation_id>/status/', views.content_generation_status_view, name='content-generation-status'),
    path('<uuid:content_generation_id>/retry/', views.retry_content_generation_view, name='content-generation-retry'),
    
    # Helper endpoints
    path('available-transcriptions/', views.available_transcriptions_view, name='available-transcriptions'),
    path('stats/', views.user_content_generation_stats_view, name='content-generation-stats'),
] 