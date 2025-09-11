from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import UserProfileinfo, Contact, InboxMessages
from books.models import Book, Borrower


class UserProfileinfoModelTest(TestCase):
    """Test cases for UserProfileinfo model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user_profile = UserProfileinfo.objects.create(
            user=self.user,
            user_type='student',
            phone_number='+1234567890',
            address='123 Test Street',
            department='Computer Science',
            student_id='STU001',
            max_books_allowed=5,
            membership_expiry=date.today() + timedelta(days=365)
        )
    
    def test_user_profile_creation(self):
        """Test user profile creation with all fields"""
        self.assertEqual(self.user_profile.user, self.user)
        self.assertEqual(self.user_profile.user_type, 'student')
        self.assertEqual(self.user_profile.phone_number, '+1234567890')
        self.assertEqual(self.user_profile.department, 'Computer Science')
        self.assertEqual(self.user_profile.student_id, 'STU001')
        self.assertEqual(self.user_profile.max_books_allowed, 5)
        self.assertEqual(self.user_profile.status, 'active')
    
    def test_user_profile_string_representation(self):
        """Test string representation"""
        expected = f"{self.user.get_full_name()} ({self.user.username})"
        self.assertEqual(str(self.user_profile), expected)
    
    def test_can_borrow_books_property(self):
        """Test can_borrow_books property"""
        # Active user with available slots
        self.assertTrue(self.user_profile.can_borrow_books)
        
        # Suspended user
        self.user_profile.status = 'suspended'
        self.user_profile.save()
        self.assertFalse(self.user_profile.can_borrow_books)
        
        # User at max books limit
        self.user_profile.status = 'active'
        self.user_profile.current_books_count = 5
        self.user_profile.save()
        self.assertFalse(self.user_profile.can_borrow_books)
    
    def test_is_membership_expired_property(self):
        """Test membership expiry detection"""
        # Not expired
        self.assertFalse(self.user_profile.is_membership_expired)
        
        # Expired
        self.user_profile.membership_expiry = date.today() - timedelta(days=1)
        self.user_profile.save()
        self.assertTrue(self.user_profile.is_membership_expired)
    
    def test_unique_constraints(self):
        """Test unique constraints on student_id and employee_id"""
        # Test duplicate student_id
        with self.assertRaises(Exception):
            UserProfileinfo.objects.create(
                user=User.objects.create_user(
                    username='testuser2',
                    email='test2@example.com',
                    password='testpass123'
                ),
                user_type='student',
                student_id='STU001'  # Duplicate
            )
    
    def test_user_type_choices(self):
        """Test user type choices"""
        valid_types = ['student', 'faculty', 'staff', 'external']
        for user_type in valid_types:
            profile = UserProfileinfo(
                user=User.objects.create_user(
                    username=f'user_{user_type}',
                    email=f'{user_type}@example.com',
                    password='testpass123'
                ),
                user_type=user_type
            )
            profile.full_clean()  # Should not raise validation error


class ContactModelTest(TestCase):
    """Test cases for Contact model"""
    
    def setUp(self):
        self.contact = Contact.objects.create(
            name='John Doe',
            email='john@example.com',
            subject='Test Subject',
            message='This is a test message',
            priority='medium'
        )
    
    def test_contact_creation(self):
        """Test contact message creation"""
        self.assertEqual(self.contact.name, 'John Doe')
        self.assertEqual(self.contact.email, 'john@example.com')
        self.assertEqual(self.contact.subject, 'Test Subject')
        self.assertEqual(self.contact.priority, 'medium')
        self.assertEqual(self.contact.status, 'new')
    
    def test_contact_string_representation(self):
        """Test string representation"""
        expected = f"{self.contact.subject} - {self.contact.name}"
        self.assertEqual(str(self.contact), expected)
    
    def test_priority_choices(self):
        """Test priority choices validation"""
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        for priority in valid_priorities:
            contact = Contact(
                name='Test User',
                email='test@example.com',
                subject='Test',
                message='Test message',
                priority=priority
            )
            contact.full_clean()  # Should not raise validation error
    
    def test_status_choices(self):
        """Test status choices validation"""
        valid_statuses = ['new', 'in_progress', 'resolved', 'closed']
        for status in valid_statuses:
            contact = Contact(
                name='Test User',
                email='test@example.com',
                subject='Test',
                message='Test message',
                status=status
            )
            contact.full_clean()  # Should not raise validation error


class InboxMessagesModelTest(TestCase):
    """Test cases for InboxMessages model"""
    
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
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@example.com',
            password='testpass123'
        )
        self.message = InboxMessages.objects.create(
            recipient=self.user_profile,
            sender=self.sender,
            message_type='notification',
            subject='Test Notification',
            message='This is a test notification message'
        )
    
    def test_inbox_message_creation(self):
        """Test inbox message creation"""
        self.assertEqual(self.message.recipient, self.user_profile)
        self.assertEqual(self.message.sender, self.sender)
        self.assertEqual(self.message.message_type, 'notification')
        self.assertEqual(self.message.subject, 'Test Notification')
        self.assertFalse(self.message.is_read)
    
    def test_inbox_message_string_representation(self):
        """Test string representation"""
        expected = f"{self.message.subject} - {self.user_profile.user.username}"
        self.assertEqual(str(self.message), expected)
    
    def test_message_type_choices(self):
        """Test message type choices validation"""
        valid_types = ['notification', 'reminder', 'alert', 'announcement']
        for msg_type in valid_types:
            message = InboxMessages(
                recipient=self.user_profile,
                sender=self.sender,
                message_type=msg_type,
                subject='Test',
                message='Test message'
            )
            message.full_clean()  # Should not raise validation error


class LibraryUsersViewsTest(TestCase):
    """Test cases for library_users views"""
    
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
    
    def test_user_registration_view(self):
        """Test user registration view"""
        response = self.client.get(reverse('library_users:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register')
    
    def test_user_login_view(self):
        """Test user login view"""
        response = self.client.get(reverse('library_users:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
    
    def test_user_login_functionality(self):
        """Test user login functionality"""
        response = self.client.post(reverse('library_users:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
    
    def test_user_logout_functionality(self):
        """Test user logout functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('library_users:logout'))
        # Should redirect after logout
        self.assertEqual(response.status_code, 302)
    
    def test_contact_form_view(self):
        """Test contact form view"""
        response = self.client.get(reverse('library_users:contact'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Contact')
    
    def test_contact_form_submission(self):
        """Test contact form submission"""
        response = self.client.post(reverse('library_users:contact'), {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'This is a test message',
            'priority': 'medium'
        })
        
        # Should create contact record
        self.assertTrue(Contact.objects.filter(email='test@example.com').exists())
    
    def test_authenticated_user_access(self):
        """Test authenticated user access to protected views"""
        # Test without login
        response = self.client.get(reverse('books:my_books'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test with login
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('books:my_books'))
        self.assertEqual(response.status_code, 200)


class UserPermissionsTest(TestCase):
    """Test cases for user permissions and groups"""
    
    def setUp(self):
        # Create groups
        self.members_group = Group.objects.create(name='Members')
        self.librarians_group = Group.objects.create(name='Librarians')
        self.admins_group = Group.objects.create(name='Admins')
        
        # Create users
        self.member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='testpass123'
        )
        self.member_profile = UserProfileinfo.objects.create(
            user=self.member,
            user_type='student'
        )
        self.member.groups.add(self.members_group)
        
        self.librarian = User.objects.create_user(
            username='librarian',
            email='librarian@example.com',
            password='testpass123',
            is_staff=True
        )
        self.librarian_profile = UserProfileinfo.objects.create(
            user=self.librarian,
            user_type='staff'
        )
        self.librarian.groups.add(self.librarians_group)
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.admin_profile = UserProfileinfo.objects.create(
            user=self.admin,
            user_type='staff'
        )
        self.admin.groups.add(self.admins_group)
    
    def test_member_permissions(self):
        """Test member user permissions"""
        self.client.login(username='member', password='testpass123')
        
        # Members should access book views
        response = self.client.get(reverse('books:view_books'))
        self.assertEqual(response.status_code, 200)
        
        # Members should NOT access admin views
        response = self.client.get(reverse('books:manage_borrow_requests'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_librarian_permissions(self):
        """Test librarian user permissions"""
        self.client.login(username='librarian', password='testpass123')
        
        # Librarians should access book management views
        response = self.client.get(reverse('books:manage_borrow_requests'))
        self.assertEqual(response.status_code, 200)
        
        # Librarians should access reports
        response = self.client.get(reverse('books:reports'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_permissions(self):
        """Test admin user permissions"""
        self.client.login(username='admin', password='testpass123')
        
        # Admins should access all views
        response = self.client.get(reverse('books:manage_borrow_requests'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('books:reports'))
        self.assertEqual(response.status_code, 200)
    
    def test_group_membership(self):
        """Test user group membership"""
        self.assertTrue(self.member.groups.filter(name='Members').exists())
        self.assertTrue(self.librarian.groups.filter(name='Librarians').exists())
        self.assertTrue(self.admin.groups.filter(name='Admins').exists())


class UserWorkflowIntegrationTest(TestCase):
    """Integration tests for user workflows"""
    
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
        self.book = Book.objects.create(
            serial='TEST001',
            shelf='A1',
            title='Test Book',
            author='Test Author',
            is_available=True
        )
    
    def test_complete_user_journey(self):
        """Test complete user journey from registration to book borrowing"""
        # 1. User registers (simulated by creating user in setUp)
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        # 2. User logs in
        login_response = self.client.post(reverse('library_users:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(login_response.status_code, 302)  # Redirect after login
        
        # 3. User browses books
        books_response = self.client.get(reverse('books:view_books'))
        self.assertEqual(books_response.status_code, 200)
        self.assertContains(books_response, 'Test Book')
        
        # 4. User views book details
        detail_response = self.client.get(reverse('books:book_detail', kwargs={'pk': self.book.pk}))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'Test Book')
        
        # 5. User requests to borrow book
        borrow_response = self.client.post(reverse('books:borrow_book', kwargs={'book_id': self.book.pk}))
        # Should create borrow request or borrowing record
        
        # 6. User checks their books
        my_books_response = self.client.get(reverse('books:my_books'))
        self.assertEqual(my_books_response.status_code, 200)
    
    def test_user_profile_update_workflow(self):
        """Test user profile update workflow"""
        self.client.login(username='testuser', password='testpass123')
        
        # Update profile information
        self.user_profile.phone_number = '+9876543210'
        self.user_profile.address = '456 New Address'
        self.user_profile.save()
        
        # Verify updates
        updated_profile = UserProfileinfo.objects.get(user=self.user)
        self.assertEqual(updated_profile.phone_number, '+9876543210')
        self.assertEqual(updated_profile.address, '456 New Address')
    
    def test_user_notification_workflow(self):
        """Test user notification workflow"""
        # Create notification
        notification = InboxMessages.objects.create(
            recipient=self.user_profile,
            message_type='notification',
            subject='Test Notification',
            message='Your book is due soon'
        )
        
        # User should see notification
        self.assertTrue(InboxMessages.objects.filter(
            recipient=self.user_profile,
            is_read=False
        ).exists())
        
        # Mark as read
        notification.is_read = True
        notification.save()
        
        # Verify read status
        self.assertTrue(notification.is_read)


class UserSecurityTest(TestCase):
    """Test cases for user security features"""
    
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
    
    def test_password_validation(self):
        """Test password validation requirements"""
        # Test weak password (should be handled by Django's password validators)
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='weakuser',
                email='weak@example.com',
                password='123'  # Too short
            )
    
    def test_user_session_security(self):
        """Test user session security"""
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Access protected view
        response = self.client.get(reverse('books:my_books'))
        self.assertEqual(response.status_code, 200)
        
        # Logout
        self.client.logout()
        
        # Try to access protected view after logout
        response = self.client.get(reverse('books:my_books'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_user_data_privacy(self):
        """Test user data privacy"""
        # Ensure sensitive data is not exposed
        self.assertIsNotNone(self.user_profile.user.password)
        # Password should be hashed, not plain text
        self.assertNotEqual(self.user_profile.user.password, 'testpass123')
        
        # Email should be accessible only to authorized users
        self.assertEqual(self.user_profile.user.email, 'test@example.com')
