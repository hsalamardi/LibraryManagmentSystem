from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from .decorators import librarian_required
import time
import psutil
import json
from datetime import datetime, timedelta
from .audit import AuditLog, SecurityEvent


@librarian_required
def performance_dashboard(request):
    """Performance monitoring dashboard for librarians and admins"""
    # Get performance metrics from cache
    metrics = cache.get('performance_metrics', [])
    aggregated = cache.get('performance_aggregated', {})
    
    # Get system health data
    system_health = get_system_health()
    
    # Get recent slow requests
    slow_requests = [m for m in metrics[-20:] if m.get('is_slow', False)]
    
    # Get database performance
    db_stats = get_database_stats()
    
    context = {
        'metrics': metrics[-50:],  # Last 50 requests
        'aggregated': aggregated,
        'system_health': system_health,
        'slow_requests': slow_requests,
        'db_stats': db_stats,
        'total_requests': len(metrics),
    }
    
    return render(request, 'books/performance_dashboard.html', context)


@librarian_required
def performance_api(request):
    """API endpoint for real-time performance data"""
    data_type = request.GET.get('type', 'metrics')
    
    if data_type == 'metrics':
        metrics = cache.get('performance_metrics', [])
        return JsonResponse({
            'metrics': metrics[-20:],  # Last 20 requests
            'timestamp': time.time()
        })
    
    elif data_type == 'aggregated':
        aggregated = cache.get('performance_aggregated', {})
        return JsonResponse(aggregated)
    
    elif data_type == 'system':
        system_health = get_system_health()
        return JsonResponse(system_health)
    
    elif data_type == 'database':
        db_stats = get_database_stats()
        return JsonResponse(db_stats)
    
    else:
        return JsonResponse({'error': 'Invalid data type'}, status=400)


@librarian_required
def security_dashboard(request):
    """Security monitoring dashboard"""
    # Get recent security events
    recent_events = SecurityEvent.objects.filter(
        timestamp__gte=datetime.now() - timedelta(days=7)
    ).order_by('-timestamp')[:50]
    
    # Get recent audit logs
    recent_audits = AuditLog.objects.filter(
        timestamp__gte=datetime.now() - timedelta(days=7)
    ).order_by('-timestamp')[:50]
    
    # Get security statistics
    security_stats = {
        'total_events': SecurityEvent.objects.count(),
        'unresolved_events': SecurityEvent.objects.filter(resolved=False).count(),
        'failed_logins': SecurityEvent.objects.filter(
            event_type='failed_login',
            timestamp__gte=datetime.now() - timedelta(days=1)
        ).count(),
        'rate_limit_violations': SecurityEvent.objects.filter(
            event_type='rate_limit_exceeded',
            timestamp__gte=datetime.now() - timedelta(days=1)
        ).count(),
    }
    
    # Get top IP addresses with security events
    from django.db.models import Count
    top_ips = SecurityEvent.objects.filter(
        timestamp__gte=datetime.now() - timedelta(days=7)
    ).values('ip_address').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'recent_events': recent_events,
        'recent_audits': recent_audits,
        'security_stats': security_stats,
        'top_ips': top_ips,
    }
    
    return render(request, 'books/security_dashboard.html', context)


@librarian_required
def system_metrics_api(request):
    """API endpoint for real-time system metrics"""
    try:
        # Get current system metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_usage('/')
        
        # Get network stats if available
        try:
            network = psutil.net_io_counters()
            network_stats = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv,
            }
        except:
            network_stats = {}
        
        # Get process information
        try:
            process = psutil.Process()
            process_stats = {
                'memory_percent': process.memory_percent(),
                'cpu_percent': process.cpu_percent(),
                'num_threads': process.num_threads(),
                'create_time': process.create_time(),
            }
        except:
            process_stats = {}
        
        metrics = {
            'timestamp': time.time(),
            'system': {
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count(),
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': network_stats,
                'process': process_stats
            },
            'cache': get_cache_stats(),
            'database': get_database_stats()
        }
        
        return JsonResponse(metrics)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'timestamp': time.time()
        }, status=500)


def get_system_health():
    """Get current system health metrics"""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_usage('/')
        
        return {
            'memory_usage': memory.percent,
            'cpu_usage': cpu_percent,
            'disk_usage': disk.percent,
            'status': 'healthy' if all([
                memory.percent < 85,
                cpu_percent < 85,
                disk.percent < 85
            ]) else 'warning',
            'timestamp': time.time()
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }


def get_database_stats():
    """Get database performance statistics"""
    try:
        # Get query count from Django's connection
        query_count = len(connection.queries)
        
        # Get database size (this is database-specific)
        db_stats = {
            'query_count': query_count,
            'connection_status': 'connected' if connection.connection else 'disconnected',
        }
        
        # Try to get database-specific stats
        try:
            with connection.cursor() as cursor:
                # For MySQL
                if 'mysql' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                    result = cursor.fetchone()
                    if result:
                        db_stats['connections'] = int(result[1])
                    
                    cursor.execute("SHOW STATUS LIKE 'Queries'")
                    result = cursor.fetchone()
                    if result:
                        db_stats['total_queries'] = int(result[1])
                
                # For PostgreSQL
                elif 'postgresql' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute("SELECT count(*) FROM pg_stat_activity")
                    result = cursor.fetchone()
                    if result:
                        db_stats['connections'] = result[0]
                
                # For SQLite
                elif 'sqlite' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute("PRAGMA database_list")
                    db_stats['database_file'] = 'sqlite'
        
        except Exception as e:
            db_stats['error'] = str(e)
        
        return db_stats
        
    except Exception as e:
        return {
            'error': str(e),
            'status': 'error'
        }


def get_cache_stats():
    """Get cache performance statistics"""
    try:
        # Test cache connectivity
        test_key = 'cache_health_test'
        cache.set(test_key, 'ok', 10)
        cache_working = cache.get(test_key) == 'ok'
        
        stats = {
            'status': 'working' if cache_working else 'error',
            'backend': str(cache.__class__.__name__),
        }
        
        # Try to get Redis-specific stats if using Redis
        try:
            if hasattr(cache, '_cache') and hasattr(cache._cache, '_client'):
                redis_client = cache._cache._client.get_client()
                redis_info = redis_client.info()
                stats.update({
                    'redis_version': redis_info.get('redis_version'),
                    'used_memory': redis_info.get('used_memory'),
                    'connected_clients': redis_info.get('connected_clients'),
                    'total_commands_processed': redis_info.get('total_commands_processed'),
                })
        except Exception:
            pass  # Redis stats not available
        
        return stats
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@librarian_required
def clear_performance_cache(request):
    """Clear performance monitoring cache"""
    if request.method == 'POST':
        try:
            cache.delete('performance_metrics')
            cache.delete('performance_aggregated')
            
            # Log the action
            AuditLog.log_action(
                user=request.user,
                action='admin_access',
                description='Cleared performance monitoring cache',
                request=request,
                severity='medium'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Performance cache cleared successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@librarian_required
def export_performance_data(request):
    """Export performance data for analysis"""
    try:
        # Get all performance metrics
        metrics = cache.get('performance_metrics', [])
        aggregated = cache.get('performance_aggregated', {})
        
        export_data = {
            'export_timestamp': time.time(),
            'metrics': metrics,
            'aggregated': aggregated,
            'system_info': {
                'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
                'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown'),
                'server_time': datetime.now().isoformat(),
            }
        }
        
        # Log the export action
        AuditLog.log_action(
            user=request.user,
            action='admin_access',
            description='Exported performance monitoring data',
            request=request,
            severity='medium'
        )
        
        response = JsonResponse(export_data)
        response['Content-Disposition'] = f'attachment; filename="performance_data_{int(time.time())}.json"'
        return response
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)