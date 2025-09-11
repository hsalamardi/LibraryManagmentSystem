"""nta_library URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.urls import path
from django.db import connection
from django.core.cache import cache
from django.views.generic import RedirectView
import time

def health_check(request):
    """Health check endpoint for Docker containers"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check cache (Redis) if configured
        try:
            cache.set('health_check', 'ok', 10)
            cache_status = cache.get('health_check') == 'ok'
        except:
            cache_status = False
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': time.time(),
            'database': 'ok',
            'cache': 'ok' if cache_status else 'unavailable',
            'version': '1.0.0'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': time.time(),
            'error': str(e)
        }, status=503)

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('', include('books.urls',namespace='Books')),
    path('library_users/', include('library_users.urls',namespace='Library')),
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('books.api_urls')),
    
    # API documentation redirect
    path('api-docs/', RedirectView.as_view(url='/api/v1/', permanent=False)),
    # path('forest', include('django_forest.urls')),  # Commented out - missing dependency
]

admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.site_title = settings.ADMIN_SITE_TITLE
