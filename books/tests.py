from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from .models import Book, Borrower, BookReservation, BorrowRequest, ReturnRequest, ThemeConfiguration
from library_users.models import UserProfileinfo
from .audit import AuditLog, SecurityEvent


class BookModelTest(TestCase):
    """Test cases for Book model"""
    
    def setUp(self):
        self.book = Book.objects.create(
            serial='TEST001',
            shelf='A1',
            title='Test Book',
            isbn='9781234567890',
            author='Test Author',
            publisher='Test Publisher',
            language='en',
            is_available=True
        )
    
    def test_book_creation(self):
        """Test book creation with required fields"""
        self.assertEqual(self.book.title, 'Test Book')
        self.assertEqual(self.book.author, 'Test Author')
        self.assertTrue(self.book.is_available)
        self.assertEqual(str(self.book), 'Test Book')
    
    def test_book_cover_image_url(self):
        """Test book cover image URL generation"""
        # Test without cover image
        self.assertEqual(self.book.get_cover_image_url(), '/static/images/default_book_cover.svg')
        
        # Test has_cover_image property
        self.assertFalse(self.book.has_cover_image)
    
    def test_book_unique_constraints(self):
        """Test unique constraints on serial and ISBN"""
        with self.assertRaises(Exception):
            Book.objects.create(
                serial='TEST001',  # Duplicate serial
                shelf='B1',
                title='Another Book',
                author='Another Author'
            )
    
    def test_book_isbn_validation(self):
        """Test ISBN field validation"""
        book = Book.objects.create(
            serial='TEST002',
            shelf='B1',
            title='ISBN Test Book',
            isbn='978-0-123456-78-9',
            author='Test Author'
        )
        self.assertEqual(book.isbn, '978-0-123456-78-9')


class BorrowerModelTest(TestCase):
    """Test cases for Borrower model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile = UserProfileinfo.objects.create(
            user=self.user,
            user_type='student',
            max_books_allowed=5
        )
        self.book = Book.objects.create(
            serial='TEST001',
            shelf='A1',
            title='Test Book',
            author='Test Author',
            is_available=True
        )
        self.borrower = Borrower.objects.create(
            book=self.book,
            borrower=self.user_profile,
            due_date=date.today() + timedelta(days=14)
        )
    
    def test_borrower_creation(self):
        """Test borrower record creation"""
        self.assertEqual(self.borrower.book, self.book)
        self.assertEqual(self.borrower.borrower, self.user_profile)
        self.assertEqual(self.borrower.status, 'borrowed')
        self.assertEqual(self.borrower.fine_amount, Decimal('0.00'))
    
    def test_is_overdue_property(self):
        """Test overdue detection"""
        # Not overdue
        self.assertFalse(self.borrower.is_overdue)
        
        # Make it overdue
        self.borrower.due_date = date.today() - timedelta(days=1)
        self.borrower.save()
        self.assertTrue(self.borrower.is_overdue)
    
    def test_calculate_fine(self):
        """Test fine calculation"""
        # Make it overdue by 3 days
        self.borrower.due_date = date.today() - timedelta(days=3)
        self.borrower.save()
        
        fine = self.borrower.calculate_fine(daily_fine=1.50)
        self.assertEqual(fine, Decimal('4.50'))  # 3 days * $1.50
    
    def test_borrower_string_representation(self):
        """Test string representation"""
        expected = f"{self.user.username} borrowed {self.book.title}"
        self.assertEqual(str(self.borrower), expected)


class BookReservationModelTest(TestCase):
    """Test cases for BookReservation model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile = UserProfileinfo.objects.create(
            user=self.user,
            user_type='student'
        )
        self.book = Book.objects.create(
            serial='TEST001',
            shelf='A1',
            title='Test Book',
            author='Test Author',
            is_available=False
        )
        self.reservation = BookReservation.objects.create(
            book=self.book,
            user=self.user_profile,
            expiry_date=timezone.now() + timedelta(days=7)
        )
    
    def test_reservation_creation(self):
        """Test reservation creation"""
        self.assertEqual(self.reservation.book, self.book)
        self.assertEqual(self.reservation.user, self.user_profile)
        self.assertEqual(self.reservation.status, 'active')
    
    def test_unique_together_constraint(self):
        """Test unique together constraint"""
        with self.assertRaises(Exception):
            BookReservation.objects.create(
                book=self.book,
                user=self.user_profile,
                status='active',  # Same book, user, and status
                expiry_date=timezone.now() + timedelta(days=7)
            )


class BookViewsTest(TestCase):
    """Test cases for Book views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile = UserProfileinfo.objects.create(
            user=self.user,
            user_type='student',
            max_books_allowed=5
        )
        self.librarian = User.objects.create_user(
            username='librarian',
            email='librarian@example.com',
            password='libpass123',
            is_staff=True
        )
        self.librarian_profile = UserProfileinfo.objects.create(
            user=self.librarian,
            user_type='staff'
        )
        self.book = Book.objects.create(
            serial='TEST001',
            shelf='A1',
            title='Test Book',
            author='Test Author',
            is_available=True
        )
    
    def test_landing_page_view(self):
        """Test landing page loads correctly"""
        response = self.client.get(reverse('books:landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Book')
    
    def test_books_list_view_authenticated(self):
        """Test books list view for authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('books:view_books'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Book')
    
    def test_books_list_view_unauthenticated(self):
        """Test books list view redirects unauthenticated users"""
        response = self.client.get(reverse('books:view_books'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_book_detail_view(self):
        """Test book detail view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('books:book_detail', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.book.title)
        self.assertContains(response, self.book.author)
    
    @patch('books.views.cache')
    def test_landing_page_caching(self, mock_cache):
        """Test that landing page uses caching"""
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        
        response = self.client.get(reverse('books:landing'))
        self.assertEqual(response.status_code, 200)
        
        # Verify cache.get was called
        mock_cache.get.assert_called()
        # Verify cache.set was called
        mock_cache.set.assert_called()
    
    def test_borrow_book_view(self):
        """Test book borrowing functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('books:borrow_book', kwargs={'book_id': self.book.pk}))
        
        # Should create a borrow request
        self.assertTrue(BorrowRequest.objects.filter(book=self.book, requester=self.user_profile).exists())
    
    def test_librarian_required_views(self):
        """Test that librarian views require proper permissions"""
        # Test with regular user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('books:manage_borrow_requests'))
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Test with librarian
        self.client.login(username='librarian', password='libpass123')
        response = self.client.get(reverse('books:manage_borrow_requests'))
        self.assertEqual(response.status_code, 200)


class SecurityTest(TestCase):
    """Test cases for security features"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile = UserProfileinfo.objects.create(
            user=self.user,
            user_type='student'
        )
    
    def test_audit_log_creation(self):
        """Test audit log creation"""
        AuditLog.log_action(
            user=self.user,
            action='login',
            description='User logged in',
            severity='low'
        )
        
        log = AuditLog.objects.first()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'login')
        self.assertEqual(log.severity, 'low')
        self.assertTrue(log.success)
    
    def test_security_event_logging(self):
        """Test security event logging"""
        # Mock request object
        request = MagicMock()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.1.1',
            'HTTP_USER_AGENT': 'Test Browser'
        }
        
        SecurityEvent.log_security_event(
            event_type='failed_login',
            request=request,
            user=self.user,
            details={'attempts': 3}
        )
        
        event = SecurityEvent.objects.first()
        self.assertEqual(event.event_type, 'failed_login')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.ip_address, '192.168.1.1')
        self.assertFalse(event.resolved)
    
    @patch('books.views.ratelimit')
    def test_rate_limiting(self, mock_ratelimit):
        """Test rate limiting on views"""
        mock_ratelimit.return_value = lambda func: func
        
        self.client.login(username='testuser', password='testpass123')
        
        # Make multiple requests to test rate limiting
        for i in range(15):
            response = self.client.post(reverse('books:borrow_book', kwargs={'book_id': 1}))
            # Should not return 429 (rate limited) in test due to mocking


class ThemeConfigurationTest(TestCase):
    """Test cases for theme configuration"""
    
    def setUp(self):
        self.theme = ThemeConfiguration.objects.create(
            name='Test Theme',
            description='A test theme',
            is_active=True,
            primary_color='#007bff',
            secondary_color='#6c757d'
        )
    
    def test_theme_creation(self):
        """Test theme configuration creation"""
        self.assertEqual(self.theme.name, 'Test Theme')
        self.assertTrue(self.theme.is_active)
        self.assertEqual(self.theme.primary_color, '#007bff')
    
    def test_get_active_theme(self):
        """Test getting active theme"""
        active_theme = ThemeConfiguration.get_active_theme()
        self.assertEqual(active_theme, self.theme)
    
    def test_theme_css_generation(self):
        """Test CSS generation from theme"""
        css = self.theme.generate_css()
        self.assertIn('--primary-color: #007bff', css)
        self.assertIn('--secondary-color: #6c757d', css)
    
    def test_theme_variables_json(self):
        """Test theme variables JSON generation"""
        variables = self.theme.to_css_variables()
        self.assertIn('primary_color', variables)
        self.assertEqual(variables['primary_color'], '#007bff')


class PerformanceTest(TestCase):
    """Test cases for performance optimizations"""
    
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile = UserProfileinfo.objects.create(
            user=self.user,
            user_type='student'
        )
        
        # Create multiple books for testing
        for i in range(10):
            Book.objects.create(
                serial=f'TEST{i:03d}',
                shelf=f'A{i}',
                title=f'Test Book {i}',
                author=f'Test Author {i}',
                is_available=True
            )
    
    def test_book_list_query_optimization(self):
        """Test that book list queries are optimized"""
        self.client.login(username='testuser', password='testpass123')
        
        with self.assertNumQueries(3):  # Should be minimal queries due to optimization
            response = self.client.get(reverse('books:view_books'))
            self.assertEqual(response.status_code, 200)
    
    @patch('books.views.cache')
    def test_dashboard_caching(self, mock_cache):
        """Test dashboard caching functionality"""
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        
        response = self.client.get(reverse('books:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Verify multiple cache operations
        self.assertGreater(mock_cache.get.call_count, 1)
        self.assertGreater(mock_cache.set.call_count, 1)


class IntegrationTest(TestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile = UserProfileinfo.objects.create(
            user=self.user,
            user_type='student',
            max_books_allowed=5
        )
        self.librarian = User.objects.create_user(
            username='librarian',
            email='librarian@example.com',
            password='libpass123',
            is_staff=True
        )
        self.librarian_profile = UserProfileinfo.objects.create(
            user=self.librarian,
            user_type='staff'
        )
        self.book = Book.objects.create(
            serial='TEST001',
            shelf='A1',
            title='Test Book',
            author='Test Author',
            is_available=True
        )
    
    def test_complete_borrow_workflow(self):
        """Test complete book borrowing workflow"""
        # 1. User requests to borrow book
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('books:borrow_book', kwargs={'book_id': self.book.pk}))
        
        # Verify borrow request created
        borrow_request = BorrowRequest.objects.get(book=self.book, requester=self.user_profile)
        self.assertEqual(borrow_request.status, 'pending')
        
        # 2. Librarian approves request
        self.client.login(username='librarian', password='libpass123')
        response = self.client.post(
            reverse('books:approve_borrow_request', kwargs={'request_id': borrow_request.pk})
        )
        
        # Verify borrowing record created
        borrowing = Borrower.objects.get(book=self.book, borrower=self.user_profile)
        self.assertEqual(borrowing.status, 'borrowed')
        
        # Verify book is no longer available
        self.book.refresh_from_db()
        self.assertFalse(self.book.is_available)
        
        # 3. User returns book
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('books:process_return_directly', kwargs={'borrowing_id': borrowing.pk})
        )
        
        # Verify book is returned
        borrowing.refresh_from_db()
        self.assertEqual(borrowing.status, 'returned')
        self.assertIsNotNone(borrowing.return_date)
        
        # Verify book is available again
        self.book.refresh_from_db()
        self.assertTrue(self.book.is_available)
    
    def test_reservation_workflow(self):
        """Test book reservation workflow"""
        # Make book unavailable
        self.book.is_available = False
        self.book.save()
        
        # User reserves book
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('books:reserve_book', kwargs={'book_id': self.book.pk}))
        
        # Verify reservation created
        reservation = BookReservation.objects.get(book=self.book, user=self.user_profile)
        self.assertEqual(reservation.status, 'active')
        
        # Verify user can see reservation in their books
        response = self.client.get(reverse('books:my_books'))
        self.assertContains(response, self.book.title)
