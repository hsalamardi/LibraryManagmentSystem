from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib import messages
from .audit import AuditLog, SecurityEvent
from django.utils import timezone
import json


def audit_action(action_type, description_template=None, severity='medium'):
    """Decorator to automatically log admin actions"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Execute the view function
            try:
                response = view_func(request, *args, **kwargs)
                
                # Log successful action
                description = description_template or f"{action_type} action performed"
                if hasattr(request, 'resolver_match') and request.resolver_match:
                    description += f" on {request.resolver_match.url_name}"
                
                AuditLog.log_action(
                    user=request.user if request.user.is_authenticated else None,
                    action=action_type,
                    description=description,
                    request=request,
                    severity=severity,
                    success=True
                )
                
                return response
                
            except Exception as e:
                # Log failed action
                description = f"Failed {action_type} action"
                AuditLog.log_action(
                    user=request.user if request.user.is_authenticated else None,
                    action=action_type,
                    description=description,
                    request=request,
                    severity='high',
                    success=False,
                    error_message=str(e)
                )
                
                # Log security event for failed admin actions
                if hasattr(request.user, 'is_staff') and request.user.is_staff:
                    SecurityEvent.log_security_event(
                        event_type='unauthorized_access',
                        request=request,
                        user=request.user,
                        details={'error': str(e), 'action': action_type}
                    )
                
                raise  # Re-raise the exception
                
        return wrapper
    return decorator


def log_admin_access(view_func):
    """Decorator to log admin panel access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Log admin access
        if request.user.is_authenticated:
            AuditLog.log_action(
                user=request.user,
                action='admin_access',
                description=f"Accessed admin panel: {request.path}",
                request=request,
                severity='medium' if request.user.is_staff else 'high'
            )
            
            # Log security event for non-staff accessing admin
            if not request.user.is_staff:
                SecurityEvent.log_security_event(
                    event_type='unauthorized_access',
                    request=request,
                    user=request.user,
                    details={'attempted_path': request.path}
                )
                messages.error(request, "Unauthorized access attempt logged.")
                return HttpResponseForbidden("Access denied")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def monitor_sensitive_operations(operation_type):
    """Decorator for monitoring sensitive operations like data exports, bulk operations"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Log the sensitive operation
            AuditLog.log_action(
                user=request.user if request.user.is_authenticated else None,
                action='admin_access',
                description=f"Sensitive operation: {operation_type}",
                request=request,
                severity='high'
            )
            
            # Additional monitoring for bulk operations
            if 'bulk' in operation_type.lower() or 'export' in operation_type.lower():
                SecurityEvent.log_security_event(
                    event_type='suspicious_activity',
                    request=request,
                    user=request.user,
                    details={
                        'operation': operation_type,
                        'timestamp': timezone.now().isoformat()
                    }
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def rate_limit_security_log(view_func):
    """Decorator to log rate limit violations"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            # Check if it's a rate limit exception
            if 'rate limit' in str(e).lower() or 'too many requests' in str(e).lower():
                SecurityEvent.log_security_event(
                    event_type='rate_limit_exceeded',
                    request=request,
                    user=request.user if request.user.is_authenticated else None,
                    details={
                        'path': request.path,
                        'method': request.method,
                        'error': str(e)
                    }
                )
            raise
    return wrapper


class SecurityMiddleware:
    """Middleware to monitor and log security events"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.suspicious_paths = [
            '/admin/auth/user/',
            '/admin/books/book/',
            '/admin/',
        ]
        self.sensitive_params = ['password', 'token', 'key', 'secret']
    
    def __call__(self, request):
        # Pre-process request
        self.log_suspicious_activity(request)
        
        response = self.get_response(request)
        
        # Post-process response
        self.log_response_anomalies(request, response)
        
        return response
    
    def log_suspicious_activity(self, request):
        """Log potentially suspicious activities"""
        # Check for suspicious paths
        if any(path in request.path for path in self.suspicious_paths):
            if not request.user.is_authenticated or not request.user.is_staff:
                SecurityEvent.log_security_event(
                    event_type='unauthorized_access',
                    request=request,
                    user=request.user if request.user.is_authenticated else None,
                    details={'attempted_path': request.path}
                )
        
        # Check for sensitive parameters in GET/POST
        sensitive_data_detected = False
        for param in self.sensitive_params:
            if param in request.GET or (hasattr(request, 'POST') and param in request.POST):
                sensitive_data_detected = True
                break
        
        if sensitive_data_detected:
            AuditLog.log_action(
                user=request.user if request.user.is_authenticated else None,
                action='admin_access',
                description=f"Request with sensitive parameters: {request.path}",
                request=request,
                severity='high'
            )
    
    def log_response_anomalies(self, request, response):
        """Log response anomalies that might indicate security issues"""
        # Log 403 Forbidden responses
        if response.status_code == 403:
            SecurityEvent.log_security_event(
                event_type='unauthorized_access',
                request=request,
                user=request.user if request.user.is_authenticated else None,
                details={
                    'status_code': response.status_code,
                    'path': request.path
                }
            )
        
        # Log 500 errors that might indicate attacks
        elif response.status_code == 500:
            AuditLog.log_action(
                user=request.user if request.user.is_authenticated else None,
                action='admin_access',
                description=f"Server error on {request.path}",
                request=request,
                severity='high',
                success=False,
                error_message=f"HTTP {response.status_code}"
            )