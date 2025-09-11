from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class AuditLog(models.Model):
    """Model to track all admin actions for security auditing"""
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('approve', 'Approve'),
        ('deny', 'Deny'),
        ('borrow', 'Borrow'),
        ('return', 'Return'),
        ('reserve', 'Reserve'),
        ('admin_access', 'Admin Access'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Who performed the action
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user_email = models.EmailField(blank=True)  # Backup in case user is deleted
    
    # What action was performed
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    
    # When and where
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # What object was affected (generic foreign key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional context
    old_values = models.JSONField(null=True, blank=True)  # Before change
    new_values = models.JSONField(null=True, blank=True)  # After change
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    
    # Success/failure
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
    
    @classmethod
    def log_action(cls, user, action, description, request=None, content_object=None, 
                   old_values=None, new_values=None, severity='medium', success=True, error_message=''):
        """Convenience method to create audit log entries"""
        
        # Extract IP and user agent from request
        ip_address = None
        user_agent = ''
        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit length
        
        # Get user email for backup
        user_email = user.email if user else ''
        
        return cls.objects.create(
            user=user,
            user_email=user_email,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            content_object=content_object,
            old_values=old_values,
            new_values=new_values,
            severity=severity,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_severity_color(self):
        """Return CSS color class for severity level"""
        colors = {
            'low': 'text-success',
            'medium': 'text-warning', 
            'high': 'text-danger',
            'critical': 'text-danger fw-bold'
        }
        return colors.get(self.severity, 'text-secondary')


class SecurityEvent(models.Model):
    """Model to track security-related events"""
    
    EVENT_TYPES = [
        ('failed_login', 'Failed Login'),
        ('account_locked', 'Account Locked'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('unauthorized_access', 'Unauthorized Access'),
        ('password_change', 'Password Change'),
        ('admin_privilege_escalation', 'Admin Privilege Escalation'),
    ]
    
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_security_events')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Security Event'
        verbose_name_plural = 'Security Events'
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['resolved', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.ip_address} - {self.timestamp}"
    
    @classmethod
    def log_security_event(cls, event_type, request, user=None, details=None):
        """Log a security event"""
        return cls.objects.create(
            event_type=event_type,
            user=user,
            ip_address=AuditLog.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            details=details or {}
        )