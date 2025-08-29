from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def user_in_group(group_name):
    """Check if user belongs to a specific group"""
    def check_group(user):
        return user.groups.filter(name=group_name).exists()
    return check_group


def is_librarian(user):
    """Check if user is a librarian"""
    return user.groups.filter(name__in=['Librarian', 'Library Admin']).exists()


def is_admin(user):
    """Check if user is a library admin"""
    return user.groups.filter(name='Library Admin').exists()


def is_member(user):
    """Check if user is at least a member"""
    return user.groups.filter(name__in=['Member', 'Librarian', 'Library Admin']).exists()


def librarian_required(view_func=None, redirect_url='/library_users/login/'):
    """Decorator to require librarian access"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=redirect_url)
        @user_passes_test(is_librarian, login_url=redirect_url)
        def _wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if view_func:
        return decorator(view_func)
    return decorator


def admin_required(view_func=None, redirect_url='/library_users/login/'):
    """Decorator to require admin access"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=redirect_url)
        @user_passes_test(is_admin, login_url=redirect_url)
        def _wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if view_func:
        return decorator(view_func)
    return decorator


def member_required(view_func=None, redirect_url='/library_users/login/'):
    """Decorator to require member access"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=redirect_url)
        @user_passes_test(is_member, login_url=redirect_url)
        def _wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if view_func:
        return decorator(view_func)
    return decorator


def check_book_access(user, book):
    """Check if user can access/modify a specific book"""
    if is_librarian(user):
        return True
    # Members can only view books
    return False


def check_borrowing_access(user, borrowing):
    """Check if user can access a specific borrowing record"""
    if is_librarian(user):
        return True
    # Users can only access their own borrowings
    return borrowing.borrower.user == user


def check_profile_access(user, profile):
    """Check if user can access/modify a specific profile"""
    if is_admin(user):
        return True
    if is_librarian(user):
        return True  # Librarians can view all profiles
    # Users can only access their own profile
    return profile.user == user


class RoleRequiredMixin:
    """Mixin for class-based views to require specific roles"""
    required_role = None  # 'member', 'librarian', or 'admin'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/library_users/login/')
        
        if self.required_role == 'admin' and not is_admin(request.user):
            messages.error(request, 'You need admin privileges to access this page.')
            return redirect('books:landing')
        elif self.required_role == 'librarian' and not is_librarian(request.user):
            messages.error(request, 'You need librarian privileges to access this page.')
            return redirect('books:landing')
        elif self.required_role == 'member' and not is_member(request.user):
            messages.error(request, 'You need to be a library member to access this page.')
            return redirect('books:landing')
        
        return super().dispatch(request, *args, **kwargs)


class LibrarianRequiredMixin(RoleRequiredMixin):
    required_role = 'librarian'


class AdminRequiredMixin(RoleRequiredMixin):
    required_role = 'admin'


class MemberRequiredMixin(RoleRequiredMixin):
    required_role = 'member'