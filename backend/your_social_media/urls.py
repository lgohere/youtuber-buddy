"""
URL configuration for your_social_media project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def health_check(request):
    """Health check endpoint for Docker"""
    return JsonResponse({'status': 'healthy', 'service': 'youtuber-buddy-backend'})

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # API Routes
    path('api/auth/', include('apps.users.urls')),
    path('api/health/', health_check, name='health_check'),
    path('api/transcriptions/', include('apps.transcriptions.urls')),
    path('api/content-generation/', include('apps.content_generation.urls')),
    
    # Alias for frontend compatibility
    path('api/content/', include('apps.content_generation.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Frontend is served separately by Nginx in production 