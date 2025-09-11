from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Book, Borrower, BookReservation, BorrowRequest, ReturnRequest, ThemeConfiguration
from library_users.models import UserProfileinfo
from datetime import date, timedelta


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfileinfo model"""
    
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfileinfo
        fields = [
            'id', 'user', 'user_type', 'status', 'phone_number', 'address',
            'department', 'student_id', 'employee_id', 'max_books_allowed',
            'current_books_count', 'total_fines', 'membership_date',
            'membership_expiry', 'full_name', 'can_borrow_books'
        ]
        read_only_fields = [
            'id', 'user', 'membership_date', 'current_books_count',
            'total_fines', 'full_name', 'can_borrow_books'
        ]
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


class BookSerializer(serializers.ModelSerializer):
    """Serializer for Book model"""
    
    cover_image_url = serializers.SerializerMethodField()
    availability_status = serializers.SerializerMethodField()
    borrow_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'serial', 'shelf', 'title', 'isbn', 'barcode', 'author',
            'publisher', 'publication_date', 'edition', 'pages', 'language',
            'dewey_code', 'main_class', 'divisions', 'sections', 'cutter_author',
            'volume', 'series', 'editor', 'translator', 'place_of_publication',
            'website', 'source', 'cover_type', 'condition', 'copy_number',
            'cover_image', 'cover_image_url', 'book_summary', 'contents',
            'keywords', 'is_available', 'availability_status', 'date_added',
            'last_updated', 'borrow_count'
        ]
        read_only_fields = [
            'id', 'date_added', 'last_updated', 'cover_image_url',
            'availability_status', 'borrow_count'
        ]
    
    def get_cover_image_url(self, obj):
        """Get book cover image URL"""
        return obj.get_cover_image_url()
    
    def get_availability_status(self, obj):
        """Get detailed availability status"""
        if obj.is_available:
            return 'available'
        else:
            # Check if it's borrowed or reserved
            active_borrowing = Borrower.objects.filter(
                book=obj,
                return_date__isnull=True
            ).first()
            
            if active_borrowing:
                if active_borrowing.due_date < date.today():
                    return 'overdue'
                return 'borrowed'
            
            return 'unavailable'
    
    def get_borrow_count(self, obj):
        """Get total number of times this book has been borrowed"""
        return obj.borrowings.count()
    
    def validate_isbn(self, value):
        """Validate ISBN format"""
        if value and len(value) not in [10, 13, 17]:  # Allow for hyphens
            raise serializers.ValidationError(
                "ISBN must be 10 or 13 digits (hyphens allowed)"
            )
        return value
    
    def validate_pages(self, value):
        """Validate page count"""
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Page count must be a positive number"
            )
        return value


class BookDetailSerializer(BookSerializer):
    """Detailed serializer for Book model with additional information"""
    
    current_borrower = serializers.SerializerMethodField()
    reservation_queue = serializers.SerializerMethodField()
    borrowing_history = serializers.SerializerMethodField()
    
    class Meta(BookSerializer.Meta):
        fields = BookSerializer.Meta.fields + [
            'current_borrower', 'reservation_queue', 'borrowing_history'
        ]
    
    def get_current_borrower(self, obj):
        """Get current borrower information"""
        if not obj.is_available:
            current_borrowing = Borrower.objects.filter(
                book=obj,
                return_date__isnull=True
            ).select_related('borrower__user').first()
            
            if current_borrowing:
                return {
                    'borrower': current_borrowing.borrower.user.get_full_name() or current_borrowing.borrower.user.username,
                    'borrow_date': current_borrowing.borrow_date,
                    'due_date': current_borrowing.due_date,
                    'is_overdue': current_borrowing.is_overdue
                }
        return None
    
    def get_reservation_queue(self, obj):
        """Get active reservations for this book"""
        reservations = BookReservation.objects.filter(
            book=obj,
            status='active'
        ).select_related('user__user').order_by('reservation_date')
        
        return [{
            'user': reservation.user.user.get_full_name() or reservation.user.user.username,
            'reservation_date': reservation.reservation_date,
            'position': idx + 1
        } for idx, reservation in enumerate(reservations)]
    
    def get_borrowing_history(self, obj):
        """Get recent borrowing history (last 5 borrowings)"""
        recent_borrowings = Borrower.objects.filter(
            book=obj
        ).select_related('borrower__user').order_by('-borrow_date')[:5]
        
        return [{
            'borrower': borrowing.borrower.user.get_full_name() or borrowing.borrower.user.username,
            'borrow_date': borrowing.borrow_date,
            'return_date': borrowing.return_date,
            'status': borrowing.status
        } for borrowing in recent_borrowings]


class BorrowerSerializer(serializers.ModelSerializer):
    """Serializer for Borrower model"""
    
    book = BookSerializer(read_only=True)
    borrower = UserProfileSerializer(read_only=True)
    days_borrowed = serializers.SerializerMethodField()
    days_until_due = serializers.SerializerMethodField()
    calculated_fine = serializers.SerializerMethodField()
    
    class Meta:
        model = Borrower
        fields = [
            'id', 'book', 'borrower', 'borrow_date', 'due_date', 'return_date',
            'status', 'notes', 'fine_amount', 'is_overdue', 'days_borrowed',
            'days_until_due', 'calculated_fine'
        ]
        read_only_fields = [
            'id', 'book', 'borrower', 'borrow_date', 'is_overdue',
            'days_borrowed', 'days_until_due', 'calculated_fine'
        ]
    
    def get_days_borrowed(self, obj):
        """Calculate days since book was borrowed"""
        return (date.today() - obj.borrow_date).days
    
    def get_days_until_due(self, obj):
        """Calculate days until due (negative if overdue)"""
        return (obj.due_date - date.today()).days
    
    def get_calculated_fine(self, obj):
        """Calculate current fine amount"""
        if obj.is_overdue and not obj.return_date:
            return float(obj.calculate_fine())
        return 0.0


class BookReservationSerializer(serializers.ModelSerializer):
    """Serializer for BookReservation model"""
    
    book = BookSerializer(read_only=True)
    user = UserProfileSerializer(read_only=True)
    queue_position = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = BookReservation
        fields = [
            'id', 'book', 'user', 'reservation_date', 'expiry_date',
            'status', 'notes', 'queue_position', 'days_until_expiry'
        ]
        read_only_fields = [
            'id', 'book', 'user', 'reservation_date', 'queue_position',
            'days_until_expiry'
        ]
    
    def get_queue_position(self, obj):
        """Get position in reservation queue"""
        if obj.status == 'active':
            earlier_reservations = BookReservation.objects.filter(
                book=obj.book,
                status='active',
                reservation_date__lt=obj.reservation_date
            ).count()
            return earlier_reservations + 1
        return None
    
    def get_days_until_expiry(self, obj):
        """Calculate days until reservation expires"""
        if obj.status == 'active':
            from django.utils import timezone
            return (obj.expiry_date - timezone.now()).days
        return None


class BorrowRequestSerializer(serializers.ModelSerializer):
    """Serializer for BorrowRequest model"""
    
    book = BookSerializer(read_only=True)
    requester = UserProfileSerializer(read_only=True)
    processed_by = UserProfileSerializer(read_only=True)
    days_pending = serializers.SerializerMethodField()
    
    class Meta:
        model = BorrowRequest
        fields = [
            'id', 'book', 'requester', 'request_date', 'requested_duration_days',
            'status', 'notes', 'admin_notes', 'processed_by', 'processed_date',
            'is_pending', 'days_pending'
        ]
        read_only_fields = [
            'id', 'book', 'requester', 'request_date', 'processed_by',
            'processed_date', 'is_pending', 'days_pending'
        ]
    
    def get_days_pending(self, obj):
        """Calculate days since request was made"""
        if obj.status == 'pending':
            from django.utils import timezone
            return (timezone.now().date() - obj.request_date.date()).days
        return None
    
    def validate_requested_duration_days(self, value):
        """Validate requested duration"""
        if value < 1 or value > 30:
            raise serializers.ValidationError(
                "Requested duration must be between 1 and 30 days"
            )
        return value


class ReturnRequestSerializer(serializers.ModelSerializer):
    """Serializer for ReturnRequest model"""
    
    borrowing = BorrowerSerializer(read_only=True)
    requester = UserProfileSerializer(read_only=True)
    processed_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = ReturnRequest
        fields = [
            'id', 'borrowing', 'requester', 'request_date', 'status',
            'notes', 'admin_notes', 'processed_by', 'processed_date',
            'is_pending'
        ]
        read_only_fields = [
            'id', 'borrowing', 'requester', 'request_date', 'processed_by',
            'processed_date', 'is_pending'
        ]


class ThemeConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for ThemeConfiguration model"""
    
    css_variables = serializers.SerializerMethodField()
    
    class Meta:
        model = ThemeConfiguration
        fields = [
            'id', 'name', 'description', 'is_active', 'primary_color',
            'secondary_color', 'accent_color', 'success_color', 'warning_color',
            'danger_color', 'info_color', 'background_primary',
            'background_secondary', 'text_primary', 'text_secondary',
            'created_at', 'updated_at', 'css_variables'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'css_variables']
    
    def get_css_variables(self, obj):
        """Get CSS variables for this theme"""
        return obj.to_css_variables()
    
    def validate(self, data):
        """Validate theme configuration"""
        # Ensure only one active theme
        if data.get('is_active', False):
            if self.instance:
                # Updating existing theme
                active_themes = ThemeConfiguration.objects.filter(
                    is_active=True
                ).exclude(id=self.instance.id)
            else:
                # Creating new theme
                active_themes = ThemeConfiguration.objects.filter(is_active=True)
            
            if active_themes.exists():
                raise serializers.ValidationError(
                    "Only one theme can be active at a time. "
                    "Please deactivate the current active theme first."
                )
        
        return data


class LibraryStatisticsSerializer(serializers.Serializer):
    """Serializer for library statistics"""
    
    total_books = serializers.IntegerField()
    available_books = serializers.IntegerField()
    borrowed_books = serializers.IntegerField()
    total_users = serializers.IntegerField()
    active_borrowings = serializers.IntegerField()
    overdue_books = serializers.IntegerField()
    active_reservations = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    
    # Popular books and categories
    popular_books = BookSerializer(many=True, read_only=True)
    popular_authors = serializers.ListField(
        child=serializers.DictField(), read_only=True
    )
    
    # Time-based statistics
    books_borrowed_today = serializers.IntegerField()
    books_returned_today = serializers.IntegerField()
    new_users_this_month = serializers.IntegerField()
    
    class Meta:
        fields = [
            'total_books', 'available_books', 'borrowed_books', 'total_users',
            'active_borrowings', 'overdue_books', 'active_reservations',
            'pending_requests', 'popular_books', 'popular_authors',
            'books_borrowed_today', 'books_returned_today', 'new_users_this_month'
        ]


class APIErrorSerializer(serializers.Serializer):
    """Serializer for API error responses"""
    
    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    errors = serializers.DictField(required=False)
    timestamp = serializers.DateTimeField()
    
    class Meta:
        fields = ['success', 'message', 'errors', 'timestamp']


class APISuccessSerializer(serializers.Serializer):
    """Serializer for API success responses"""
    
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = serializers.DictField(required=False)
    timestamp = serializers.DateTimeField()
    
    class Meta:
        fields = ['success', 'message', 'data', 'timestamp']