from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from . import api_views
from . import dashboard_views, monitoring_views, views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'books', api_views.BookViewSet, basename='api-books')
router.register(r'borrowings', api_views.BorrowerViewSet, basename='api-borrowings')

# API URL patterns
urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom API endpoints
    path('health/', api_views.api_health_check, name='api-health'),
    path('statistics/', api_views.api_statistics, name='api-statistics'),
    path('analytics/', dashboard_views.analytics_api, name='analytics_api'),
    path('performance/', monitoring_views.performance_api, name='performance_api'),
    path('system-metrics/', monitoring_views.system_metrics_api, name='system_metrics_api'),
    path('barcode-lookup/', views.barcode_lookup_api, name='barcode_lookup_api'),
    
    # Authentication endpoints
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]