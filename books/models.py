from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from library_users.models import UserProfileinfo
from datetime import date

# Create your models here.

class Book(models.Model):
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
    ]
    
    COVER_TYPE_CHOICES = [
        ('hardcover', 'Hardcover'),
        ('paperback', 'Paperback'),
        ('spiral', 'Spiral Bound'),
        ('digital', 'Digital'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('fr', 'French'),
        ('es', 'Spanish'),
        ('de', 'German'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    serial = models.CharField(max_length=20, unique=True, help_text="Unique serial number for the book")
    shelf = models.CharField(max_length=20, help_text="Shelf location")
    title = models.CharField(max_length=500, help_text="Book title")
    isbn = models.CharField(max_length=17, unique=True, null=True, blank=True, help_text="ISBN-13 format")
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="Barcode for scanning")
    author = models.CharField(max_length=500, help_text="Primary author(s)")
    
    # Publication Details
    publisher = models.CharField(max_length=200, null=True, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    edition = models.CharField(max_length=100, null=True, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    
    # Classification
    dewey_code = models.CharField(max_length=20, null=True, blank=True, help_text="Dewey Decimal Classification")
    main_class = models.CharField(max_length=100, null=True, blank=True)
    divisions = models.CharField(max_length=100, null=True, blank=True)
    sections = models.CharField(max_length=100, null=True, blank=True)
    cutter_author = models.CharField(max_length=100, null=True, blank=True)
    
    # Additional Information
    volume = models.CharField(max_length=50, null=True, blank=True)
    series = models.CharField(max_length=200, null=True, blank=True)
    editor = models.CharField(max_length=200, null=True, blank=True)
    translator = models.CharField(max_length=200, null=True, blank=True)
    place_of_publication = models.CharField(max_length=100, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)
    
    # Physical Properties
    cover_type = models.CharField(max_length=20, choices=COVER_TYPE_CHOICES, default='paperback')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    copy_number = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True, help_text="Book cover image")
    
    # Content
    book_summary = models.TextField(null=True, blank=True)
    contents = models.TextField(null=True, blank=True, help_text="Table of contents")
    keywords = models.TextField(null=True, blank=True, help_text="Comma-separated keywords")
    
    # Status
    is_available = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def get_cover_image_url(self):
        """Return cover image URL or default placeholder"""
        if self.cover_image and hasattr(self.cover_image, 'url'):
            return self.cover_image.url
        return '/static/images/default_book_cover.svg'
    
    @property
    def has_cover_image(self):
        """Check if book has a cover image"""
        return bool(self.cover_image)
    
    class Meta:
        ordering = ['title']
        verbose_name = 'Book'
        verbose_name_plural = 'Books'


class Borrower(models.Model):
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('lost', 'Lost'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrowings')
    borrower = models.ForeignKey(UserProfileinfo, on_delete=models.CASCADE, related_name='borrowed_books')
    borrow_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')
    notes = models.TextField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.book.title} - {self.borrower.user.username}"
    
    @property
    def is_overdue(self):
        from datetime import date
        return self.due_date < date.today() and self.status == 'borrowed'
    
    def calculate_fine(self, daily_fine=1.00):
        """Calculate fine for overdue books"""
        if self.is_overdue:
            from datetime import date
            overdue_days = (date.today() - self.due_date).days
            return overdue_days * daily_fine
        return 0.00
    
    class Meta:
        ordering = ['-borrow_date']
        verbose_name = 'Book Borrowing'
        verbose_name_plural = 'Book Borrowings'


class BookReservation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    user = models.ForeignKey(UserProfileinfo, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.book.title} - {self.user.user.username} ({self.status})"
    
    class Meta:
        ordering = ['-reservation_date']
        unique_together = ['book', 'user', 'status']
        verbose_name = 'Book Reservation'
        verbose_name_plural = 'Book Reservations'