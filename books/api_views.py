from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.versioning import URLPathVersioning
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
import logging

from .models import Book, Borrower, BookReservation, BorrowRequest, ReturnRequest
from library_users.models import UserProfileinfo
from .serializers import (
    BookSerializer, BorrowerSerializer, BookReservationSerializer,
    BorrowRequestSerializer, ReturnRequestSerializer, BookDetailSerializer
)
from .audit import AuditLog
from .permissions import IsLibrarianOrReadOnly, IsOwnerOrLibrarian

# Set up API logger
api_logger = logging.getLogger('api')


class APIResponseMixin:
    """Mixin to provide consistent API responses"""
    
    def success_response(self, data=None, message="Success", status_code=status.HTTP_200_OK):
        """Return a standardized success response"""
        response_data = {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': cache.get('current_timestamp', None)
        }
        return Response(response_data, status=status_code)
    
    def error_response(self, message="An error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Return a standardized error response"""
        response_data = {
            'success': False,
            'message': message,
            'errors': errors,
            'timestamp': cache.get('current_timestamp', None)
        }
        return Response(response_data, status=status_code)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API responses"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'pagination': {
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'page_size': self.page_size,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
            },
            'data': data
        })


class APIRateThrottle(UserRateThrottle):
    """Custom rate throttling for API endpoints"""
    scope = 'api'
    rate = '100/hour'


class APIAnonRateThrottle(AnonRateThrottle):
    """Custom rate throttling for anonymous API users"""
    scope = 'api_anon'
    rate = '20/hour'


@method_decorator(ratelimit(key='user', rate='100/h', method='GET', block=True), name='list')
@method_decorator(ratelimit(key='user', rate='50/h', method='POST', block=True), name='create')
class BookViewSet(viewsets.ModelViewSet, APIResponseMixin):
    """API ViewSet for Book management with full CRUD operations"""
    
    queryset = Book.objects.select_related().all()
    serializer_class = BookSerializer
    permission_classes = [IsLibrarianOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_available', 'language', 'main_class', 'author']
    search_fields = ['title', 'author', 'isbn', 'keywords', 'book_summary']
    ordering_fields = ['title', 'author', 'date_added', 'publication_date']
    ordering = ['title']
    throttle_classes = [APIRateThrottle, APIAnonRateThrottle]
    versioning_class = URLPathVersioning
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return BookDetailSerializer
        return BookSerializer
    
    def get_queryset(self):
        """Optimize queryset based on action"""
        queryset = Book.objects.select_related()
        
        # Add caching for list view
        if self.action == 'list':
            cache_key = f'api_books_list_{self.request.GET.urlencode()}'
            cached_ids = cache.get(cache_key)
            if cached_ids is not None:
                return queryset.filter(id__in=cached_ids)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List books with caching"""
        # Try to get from cache first
        cache_key = f'api_books_list_{request.GET.urlencode()}'
        cached_response = cache.get(cache_key + '_response')
        
        if cached_response is not None:
            api_logger.info(f"API: Books list served from cache for user {request.user}")
            return Response(cached_response)
        
        # Get fresh data
        response = super().list(request, *args, **kwargs)
        
        # Cache the response for 5 minutes
        if response.status_code == 200:
            cache.set(cache_key + '_response', response.data, 300)
            # Cache the IDs for queryset optimization
            book_ids = [book['id'] for book in response.data.get('data', [])]
            cache.set(cache_key, book_ids, 300)
        
        api_logger.info(f"API: Books list generated for user {request.user}")
        return response
    
    def create(self, request, *args, **kwargs):
        """Create a new book with audit logging"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            book = serializer.save()
            
            # Log the creation
            AuditLog.log_action(
                user=request.user,
                action='create',
                description=f"Created book: {book.title}",
                request=request,
                content_object=book,
                new_values=serializer.data,
                severity='medium'
            )
            
            # Clear relevant caches
            cache.delete_pattern('api_books_list_*')
            
            api_logger.info(f"API: Book created - {book.title} by user {request.user}")
            return self.success_response(
                data=serializer.data,
                message="Book created successfully",
                status_code=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            api_logger.error(f"API: Book creation failed for user {request.user}: {str(e)}")
            return self.error_response(
                message="Failed to create book",
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        """Update book with audit logging"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_data = BookSerializer(instance).data
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            book = serializer.save()
            
            # Log the update
            AuditLog.log_action(
                user=request.user,
                action='update',
                description=f"Updated book: {book.title}",
                request=request,
                content_object=book,
                old_values=old_data,
                new_values=serializer.data,
                severity='medium'
            )
            
            # Clear relevant caches
            cache.delete_pattern('api_books_*')
            
            api_logger.info(f"API: Book updated - {book.title} by user {request.user}")
            return self.success_response(
                data=serializer.data,
                message="Book updated successfully"
            )
            
        except Exception as e:
            api_logger.error(f"API: Book update failed for user {request.user}: {str(e)}")
            return self.error_response(
                message="Failed to update book",
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def borrow(self, request, pk=None):
        """Request to borrow a book"""
        book = self.get_object()
        
        try:
            user_profile = UserProfileinfo.objects.get(user=request.user)
        except UserProfileinfo.DoesNotExist:
            return self.error_response(
                message="User profile not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user can borrow books
        if not user_profile.can_borrow_books:
            return self.error_response(
                message="You are not eligible to borrow books",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check if book is available
        if not book.is_available:
            return self.error_response(
                message="Book is not available for borrowing",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already has this book
        existing_borrow = Borrower.objects.filter(
            book=book,
            borrower=user_profile,
            return_date__isnull=True
        ).exists()
        
        if existing_borrow:
            return self.error_response(
                message="You have already borrowed this book",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create borrow request
        borrow_request = BorrowRequest.objects.create(
            book=book,
            requester=user_profile,
            requested_duration_days=request.data.get('duration_days', 14),
            notes=request.data.get('notes', '')
        )
        
        # Log the action
        AuditLog.log_action(
            user=request.user,
            action='borrow',
            description=f"Requested to borrow book: {book.title}",
            request=request,
            content_object=book,
            severity='low'
        )
        
        api_logger.info(f"API: Borrow request created for book {book.title} by user {request.user}")
        return self.success_response(
            data=BorrowRequestSerializer(borrow_request).data,
            message="Borrow request submitted successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reserve(self, request, pk=None):
        """Reserve a book"""
        book = self.get_object()
        
        try:
            user_profile = UserProfileinfo.objects.get(user=request.user)
        except UserProfileinfo.DoesNotExist:
            return self.error_response(
                message="User profile not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if book is available (can't reserve available books)
        if book.is_available:
            return self.error_response(
                message="Book is available for borrowing, no need to reserve",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already has a reservation
        existing_reservation = BookReservation.objects.filter(
            book=book,
            user=user_profile,
            status='active'
        ).exists()
        
        if existing_reservation:
            return self.error_response(
                message="You already have an active reservation for this book",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create reservation
        from datetime import timedelta
        from django.utils import timezone
        
        reservation = BookReservation.objects.create(
            book=book,
            user=user_profile,
            expiry_date=timezone.now() + timedelta(days=7),
            notes=request.data.get('notes', '')
        )
        
        # Log the action
        AuditLog.log_action(
            user=request.user,
            action='reserve',
            description=f"Reserved book: {book.title}",
            request=request,
            content_object=book,
            severity='low'
        )
        
        api_logger.info(f"API: Book reserved - {book.title} by user {request.user}")
        return self.success_response(
            data=BookReservationSerializer(reservation).data,
            message="Book reserved successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get only available books"""
        available_books = self.get_queryset().filter(is_available=True)
        page = self.paginate_queryset(available_books)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(available_books, many=True)
        return self.success_response(data=serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular books based on borrow count"""
        from django.db.models import Count
        
        popular_books = self.get_queryset().annotate(
            borrow_count=Count('borrowings')
        ).filter(borrow_count__gt=0).order_by('-borrow_count')[:20]
        
        serializer = self.get_serializer(popular_books, many=True)
        return self.success_response(data=serializer.data)


@method_decorator(ratelimit(key='user', rate='50/h', method='GET', block=True), name='list')
class BorrowerViewSet(viewsets.ReadOnlyModelViewSet, APIResponseMixin):
    """API ViewSet for Borrower records (read-only)"""
    
    queryset = Borrower.objects.select_related('book', 'borrower__user').all()
    serializer_class = BorrowerSerializer
    permission_classes = [IsOwnerOrLibrarian]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'book', 'borrower']
    ordering_fields = ['borrow_date', 'due_date', 'return_date']
    ordering = ['-borrow_date']
    throttle_classes = [APIRateThrottle]
    
    def get_queryset(self):
        """Filter borrowings based on user permissions"""
        queryset = super().get_queryset()
        
        # Non-staff users can only see their own borrowings
        if not self.request.user.is_staff:
            try:
                user_profile = UserProfileinfo.objects.get(user=self.request.user)
                queryset = queryset.filter(borrower=user_profile)
            except UserProfileinfo.DoesNotExist:
                return queryset.none()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue borrowings"""
        from datetime import date
        
        overdue_borrowings = self.get_queryset().filter(
            due_date__lt=date.today(),
            return_date__isnull=True
        )
        
        page = self.paginate_queryset(overdue_borrowings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(overdue_borrowings, many=True)
        return self.success_response(data=serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='20/h', method='GET', block=True)
def api_health_check(request):
    """API health check endpoint"""
    try:
        # Test database connectivity
        book_count = Book.objects.count()
        
        # Test cache connectivity
        cache.set('api_health_test', 'ok', 10)
        cache_working = cache.get('api_health_test') == 'ok'
        
        health_data = {
            'status': 'healthy',
            'timestamp': cache.get('current_timestamp'),
            'database': {
                'status': 'connected',
                'book_count': book_count
            },
            'cache': {
                'status': 'working' if cache_working else 'error'
            },
            'api_version': 'v1'
        }
        
        return Response({
            'success': True,
            'data': health_data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'API health check failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@cache_page(60 * 15)  # Cache for 15 minutes
def api_statistics(request):
    """Get library statistics via API"""
    try:
        stats = {
            'books': {
                'total': Book.objects.count(),
                'available': Book.objects.filter(is_available=True).count(),
                'borrowed': Book.objects.filter(is_available=False).count(),
            },
            'borrowings': {
                'active': Borrower.objects.filter(return_date__isnull=True).count(),
                'overdue': Borrower.objects.filter(
                    return_date__isnull=True,
                    due_date__lt=timezone.now().date()
                ).count(),
            },
            'reservations': {
                'active': BookReservation.objects.filter(status='active').count(),
            },
            'users': {
                'total': UserProfileinfo.objects.count(),
                'active': UserProfileinfo.objects.filter(status='active').count(),
            }
        }
        
        return Response({
            'success': True,
            'data': stats,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Failed to retrieve statistics',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)