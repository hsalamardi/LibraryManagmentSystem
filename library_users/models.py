from django.db import models
from django.contrib.auth.models import User, Group
from django.core.validators import RegexValidator
from datetime import date

# Create your models here.

class UserProfileinfo(models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
        ('external', 'External Member'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
        ('pending', 'Pending Approval'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Personal Information
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    address = models.TextField(max_length=500, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Academic/Professional Information
    department = models.CharField(max_length=100, blank=True)
    student_id = models.CharField(max_length=20, blank=True, unique=True, null=True)
    employee_id = models.CharField(max_length=20, blank=True, unique=True, null=True)
    
    # Library Information
    profile_image = models.ImageField(upload_to='profile_pics', blank=True)
    membership_date = models.DateField(auto_now_add=True)
    membership_expiry = models.DateField(null=True, blank=True)
    max_books_allowed = models.PositiveIntegerField(default=5)
    current_books_count = models.PositiveIntegerField(default=0)
    total_fines = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.username})"
    
    @property
    def can_borrow_books(self):
        return (self.status == 'active' and 
                self.current_books_count < self.max_books_allowed and
                self.total_fines < 50.00)  # Max fine threshold
    
    @property
    def is_membership_expired(self):
        if self.membership_expiry:
            return self.membership_expiry < date.today()
        return False
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class Contact(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200, default='General Inquiry')
    message = models.TextField(max_length=1000)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_contacts')
    response = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'


class InboxMessages(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('notification', 'Notification'),
        ('reminder', 'Reminder'),
        ('alert', 'Alert'),
        ('announcement', 'Announcement'),
    ]
    
    recipient = models.ForeignKey(UserProfileinfo, on_delete=models.CASCADE, related_name='inbox_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='notification')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.subject} - {self.recipient.user.username}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inbox Message'
        verbose_name_plural = 'Inbox Messages'
        
