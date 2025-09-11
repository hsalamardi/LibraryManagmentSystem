from rest_framework import permissions
from library_users.models import UserProfileinfo


class IsLibrarianOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow librarians to edit objects."""
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions are only allowed to librarians and admins
        return request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.groups.filter(name='Librarians').exists() or
            request.user.groups.filter(name='Admins').exists()
        )
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions are only allowed to librarians and admins
        return request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.groups.filter(name='Librarians').exists() or
            request.user.groups.filter(name='Admins').exists()
        )


class IsOwnerOrLibrarian(permissions.BasePermission):
    """Custom permission to allow users to view their own records or librarians to view all."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Librarians and admins can access all objects
        if request.user.is_staff or \
           request.user.groups.filter(name__in=['Librarians', 'Admins']).exists():
            return True
        
        # Users can only access their own records
        try:
            user_profile = UserProfileinfo.objects.get(user=request.user)
            
            # Check if the object belongs to the user
            if hasattr(obj, 'borrower'):
                return obj.borrower == user_profile
            elif hasattr(obj, 'user'):
                return obj.user == user_profile
            elif hasattr(obj, 'requester'):
                return obj.requester == user_profile
            
        except UserProfileinfo.DoesNotExist:
            return False
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow admins to edit objects."""
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions are only allowed to admins
        return request.user.is_authenticated and (
            request.user.is_superuser or
            request.user.groups.filter(name='Admins').exists()
        )
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions are only allowed to admins
        return request.user.is_authenticated and (
            request.user.is_superuser or
            request.user.groups.filter(name='Admins').exists()
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to allow users to edit their own objects only."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        try:
            user_profile = UserProfileinfo.objects.get(user=request.user)
            
            # Check if the object belongs to the user
            if hasattr(obj, 'user'):
                return obj.user == user_profile
            elif hasattr(obj, 'requester'):
                return obj.requester == user_profile
            elif hasattr(obj, 'borrower'):
                return obj.borrower == user_profile
            
        except UserProfileinfo.DoesNotExist:
            return False
        
        return False


class CanBorrowBooks(permissions.BasePermission):
    """Custom permission to check if user can borrow books."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            user_profile = UserProfileinfo.objects.get(user=request.user)
            return user_profile.can_borrow_books
        except UserProfileinfo.DoesNotExist:
            return False


class IsActiveUser(permissions.BasePermission):
    """Custom permission to check if user profile is active."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            user_profile = UserProfileinfo.objects.get(user=request.user)
            return user_profile.status == 'active'
        except UserProfileinfo.DoesNotExist:
            return False


class HasValidMembership(permissions.BasePermission):
    """Custom permission to check if user has valid membership."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            user_profile = UserProfileinfo.objects.get(user=request.user)
            return not user_profile.is_membership_expired
        except UserProfileinfo.DoesNotExist:
            return False


class CanAccessReports(permissions.BasePermission):
    """Custom permission for accessing reports and analytics."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Only librarians and admins can access reports
        return (
            request.user.is_staff or
            request.user.groups.filter(name__in=['Librarians', 'Admins']).exists()
        )


class CanManageUsers(permissions.BasePermission):
    """Custom permission for user management operations."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Only admins can manage users
        return (
            request.user.is_superuser or
            request.user.groups.filter(name='Admins').exists()
        )


class CanAccessMonitoring(permissions.BasePermission):
    """Custom permission for accessing monitoring and performance data."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Only librarians and admins can access monitoring
        return (
            request.user.is_staff or
            request.user.groups.filter(name__in=['Librarians', 'Admins']).exists()
        )


class APIKeyPermission(permissions.BasePermission):
    """Custom permission for API key authentication."""
    
    def has_permission(self, request, view):
        # Check for API key in headers
        api_key = request.META.get('HTTP_X_API_KEY')
        
        if not api_key:
            return False
        
        # Validate API key (you would implement your own validation logic)
        # For now, we'll just check if it's not empty
        return bool(api_key)


class ThrottledPermission(permissions.BasePermission):
    """Custom permission that works with rate limiting."""
    
    def has_permission(self, request, view):
        # This permission works in conjunction with rate limiting
        # It allows the request but the rate limiting will handle throttling
        return request.user.is_authenticated
    
    def get_throttle_key(self, request, view):
        """Generate throttle key based on user type."""
        if request.user.is_authenticated:
            if request.user.is_staff:
                return f'staff_{request.user.id}'
            else:
                return f'user_{request.user.id}'
        return f'anon_{request.META.get("REMOTE_ADDR", "unknown")}'


class DynamicPermission(permissions.BasePermission):
    """Dynamic permission that can be configured per view."""
    
    def __init__(self, required_groups=None, required_permissions=None, allow_staff=True):
        self.required_groups = required_groups or []
        self.required_permissions = required_permissions or []
        self.allow_staff = allow_staff
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow staff if configured
        if self.allow_staff and request.user.is_staff:
            return True
        
        # Check required groups
        if self.required_groups:
            user_groups = request.user.groups.values_list('name', flat=True)
            if not any(group in user_groups for group in self.required_groups):
                return False
        
        # Check required permissions
        if self.required_permissions:
            for permission in self.required_permissions:
                if not request.user.has_perm(permission):
                    return False
        
        return True


class ConditionalPermission(permissions.BasePermission):
    """Permission that applies different rules based on conditions."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Different permissions for different HTTP methods
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            # Read operations - allow all authenticated users
            return True
        elif request.method in ['POST']:
            # Create operations - require active membership
            try:
                user_profile = UserProfileinfo.objects.get(user=request.user)
                return user_profile.status == 'active' and not user_profile.is_membership_expired
            except UserProfileinfo.DoesNotExist:
                return False
        elif request.method in ['PUT', 'PATCH', 'DELETE']:
            # Update/Delete operations - require librarian or admin
            return (
                request.user.is_staff or
                request.user.groups.filter(name__in=['Librarians', 'Admins']).exists()
            )
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Apply object-level permissions
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For modifications, check ownership or staff status
        if request.user.is_staff or \
           request.user.groups.filter(name__in=['Librarians', 'Admins']).exists():
            return True
        
        # Check if user owns the object
        try:
            user_profile = UserProfileinfo.objects.get(user=request.user)
            if hasattr(obj, 'user'):
                return obj.user == user_profile
            elif hasattr(obj, 'borrower'):
                return obj.borrower == user_profile
            elif hasattr(obj, 'requester'):
                return obj.requester == user_profile
        except UserProfileinfo.DoesNotExist:
            pass
        
        return False