import time
import logging
import psutil
from django.db import connection
from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .audit import AuditLog

# Set up logger for performance monitoring
performance_logger = logging.getLogger('performance')


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """Middleware to monitor application performance and system metrics"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Start timing the request"""
        request._start_time = time.time()
        request._start_queries = len(connection.queries)
        
        # Track system metrics at request start
        request._start_memory = psutil.virtual_memory().percent
        request._start_cpu = psutil.cpu_percent()
        
        return None
    
    def process_response(self, request, response):
        """Log performance metrics after request completion"""
        if not hasattr(request, '_start_time'):
            return response
        
        # Calculate timing metrics
        total_time = time.time() - request._start_time
        query_count = len(connection.queries) - request._start_queries
        
        # Calculate system metrics
        end_memory = psutil.virtual_memory().percent
        end_cpu = psutil.cpu_percent()
        memory_delta = end_memory - request._start_memory
        cpu_delta = end_cpu - request._start_cpu
        
        # Determine if this is a slow request
        is_slow = total_time > getattr(settings, 'SLOW_REQUEST_THRESHOLD', 2.0)
        has_many_queries = query_count > getattr(settings, 'MAX_QUERIES_THRESHOLD', 20)
        
        # Log performance data
        performance_data = {
            'path': request.path,
            'method': request.method,
            'response_time': round(total_time * 1000, 2),  # Convert to milliseconds
            'query_count': query_count,
            'status_code': response.status_code,
            'memory_usage': end_memory,
            'memory_delta': round(memory_delta, 2),
            'cpu_usage': end_cpu,
            'cpu_delta': round(cpu_delta, 2),
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'is_slow': is_slow,
            'has_many_queries': has_many_queries
        }
        
        # Log to performance logger
        log_level = logging.WARNING if (is_slow or has_many_queries) else logging.INFO
        performance_logger.log(
            log_level,
            f"Performance: {request.method} {request.path} - "
            f"{performance_data['response_time']}ms, "
            f"{query_count} queries, "
            f"Status: {response.status_code}",
            extra=performance_data
        )
        
        # Store metrics in cache for dashboard
        self._store_metrics_in_cache(performance_data)
        
        # Log slow requests to audit log
        if is_slow or has_many_queries:
            self._log_slow_request(request, performance_data)
        
        # Add performance headers for debugging (only in DEBUG mode)
        if settings.DEBUG:
            response['X-Response-Time'] = f"{performance_data['response_time']}ms"
            response['X-Query-Count'] = str(query_count)
            response['X-Memory-Usage'] = f"{end_memory}%"
        
        return response
    
    def _store_metrics_in_cache(self, performance_data):
        """Store performance metrics in cache for dashboard display"""
        try:
            # Store recent performance data (last 100 requests)
            cache_key = 'performance_metrics'
            metrics_list = cache.get(cache_key, [])
            
            # Add timestamp
            performance_data['timestamp'] = time.time()
            
            # Add to list and keep only last 100 entries
            metrics_list.append(performance_data)
            if len(metrics_list) > 100:
                metrics_list = metrics_list[-100:]
            
            # Store back in cache for 1 hour
            cache.set(cache_key, metrics_list, 3600)
            
            # Store aggregated metrics
            self._update_aggregated_metrics(performance_data)
            
        except Exception as e:
            performance_logger.error(f"Failed to store metrics in cache: {e}")
    
    def _update_aggregated_metrics(self, performance_data):
        """Update aggregated performance metrics"""
        try:
            # Get current aggregated data
            agg_key = 'performance_aggregated'
            agg_data = cache.get(agg_key, {
                'total_requests': 0,
                'avg_response_time': 0,
                'slow_requests': 0,
                'total_queries': 0,
                'error_count': 0,
                'paths': {}
            })
            
            # Update counters
            agg_data['total_requests'] += 1
            agg_data['total_queries'] += performance_data['query_count']
            
            # Update average response time
            current_avg = agg_data['avg_response_time']
            new_avg = ((current_avg * (agg_data['total_requests'] - 1)) + 
                      performance_data['response_time']) / agg_data['total_requests']
            agg_data['avg_response_time'] = round(new_avg, 2)
            
            # Count slow requests
            if performance_data['is_slow']:
                agg_data['slow_requests'] += 1
            
            # Count errors
            if performance_data['status_code'] >= 400:
                agg_data['error_count'] += 1
            
            # Track per-path metrics
            path = performance_data['path']
            if path not in agg_data['paths']:
                agg_data['paths'][path] = {
                    'count': 0,
                    'avg_time': 0,
                    'slow_count': 0
                }
            
            path_data = agg_data['paths'][path]
            path_data['count'] += 1
            path_avg = ((path_data['avg_time'] * (path_data['count'] - 1)) + 
                       performance_data['response_time']) / path_data['count']
            path_data['avg_time'] = round(path_avg, 2)
            
            if performance_data['is_slow']:
                path_data['slow_count'] += 1
            
            # Store aggregated data for 24 hours
            cache.set(agg_key, agg_data, 86400)
            
        except Exception as e:
            performance_logger.error(f"Failed to update aggregated metrics: {e}")
    
    def _log_slow_request(self, request, performance_data):
        """Log slow requests to audit log for investigation"""
        try:
            description = (
                f"Slow request detected: {request.method} {request.path} - "
                f"{performance_data['response_time']}ms, "
                f"{performance_data['query_count']} queries"
            )
            
            AuditLog.log_action(
                user=request.user if request.user.is_authenticated else None,
                action='admin_access',
                description=description,
                request=request,
                severity='medium',
                success=True,
                old_values=None,
                new_values=performance_data
            )
        except Exception as e:
            performance_logger.error(f"Failed to log slow request: {e}")


class SystemHealthMiddleware(MiddlewareMixin):
    """Middleware to monitor system health and provide health check endpoint"""
    
    def process_request(self, request):
        """Handle health check requests"""
        if request.path == '/health/':
            return self._health_check_response()
        return None
    
    def _health_check_response(self):
        """Generate health check response with system metrics"""
        try:
            # Get system metrics
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Check database connectivity
            db_healthy = self._check_database_health()
            
            # Check cache connectivity
            cache_healthy = self._check_cache_health()
            
            # Determine overall health
            is_healthy = (
                memory.percent < 90 and
                disk.percent < 90 and
                cpu_percent < 90 and
                db_healthy and
                cache_healthy
            )
            
            health_data = {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'timestamp': time.time(),
                'system': {
                    'memory_usage': memory.percent,
                    'disk_usage': disk.percent,
                    'cpu_usage': cpu_percent,
                },
                'services': {
                    'database': 'healthy' if db_healthy else 'unhealthy',
                    'cache': 'healthy' if cache_healthy else 'unhealthy',
                },
                'version': getattr(settings, 'VERSION', '1.0.0')
            }
            
            status_code = 200 if is_healthy else 503
            return JsonResponse(health_data, status=status_code)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }, status=500)
    
    def _check_database_health(self):
        """Check database connectivity"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                return True
        except Exception:
            return False
    
    def _check_cache_health(self):
        """Check cache connectivity"""
        try:
            cache.set('health_check', 'ok', 10)
            return cache.get('health_check') == 'ok'
        except Exception:
            return False


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log all requests for security and debugging"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('requests')
        super().__init__(get_response)
    
    def process_request(self, request):
        """Log incoming requests"""
        # Skip logging for static files and health checks
        if self._should_skip_logging(request):
            return None
        
        log_data = {
            'method': request.method,
            'path': request.path,
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            'timestamp': time.time()
        }
        
        self.logger.info(
            f"Request: {request.method} {request.path} from {log_data['ip']}",
            extra=log_data
        )
        
        return None
    
    def _should_skip_logging(self, request):
        """Determine if request should be skipped from logging"""
        skip_paths = ['/static/', '/media/', '/favicon.ico', '/health/']
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')