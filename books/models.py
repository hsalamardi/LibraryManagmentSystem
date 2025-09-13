from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
from library_users.models import UserProfileinfo
from datetime import date, timedelta
import uuid

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

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
    serial = models.CharField(max_length=20, help_text="Unique serial number for the book")
    shelf = models.CharField(max_length=20, help_text="Shelf location", db_index=True)
    title = models.CharField(max_length=500, help_text="Book title", db_index=True)
    isbn = models.CharField(max_length=17, null=True, blank=True, help_text="ISBN-13 format", db_index=True)
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="Barcode for scanning", db_index=True)
    author = models.CharField(max_length=500, help_text="Primary author(s)", db_index=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    
    # Publication Details
    publisher = models.CharField(max_length=200, null=True, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    edition = models.CharField(max_length=100, null=True, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en', db_index=True)
    
    # Classification
    dewey_code = models.CharField(max_length=20, null=True, blank=True, help_text="Dewey Decimal Classification", db_index=True)
    main_class = models.CharField(max_length=100, null=True, blank=True, db_index=True)
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
    is_available = models.BooleanField(default=True, db_index=True)
    date_added = models.DateTimeField(auto_now_add=True, db_index=True)
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
    borrow_date = models.DateField(auto_now_add=True, db_index=True)
    due_date = models.DateField(db_index=True)
    return_date = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed', db_index=True)
    notes = models.TextField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, db_index=True)
    
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


class BorrowRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('cancelled', 'Cancelled'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_requests')
    requester = models.ForeignKey(UserProfileinfo, on_delete=models.CASCADE, related_name='borrow_requests')
    request_date = models.DateTimeField(auto_now_add=True)
    requested_duration_days = models.PositiveIntegerField(default=14, help_text="Number of days to borrow")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(null=True, blank=True, help_text="Additional notes from requester")
    admin_notes = models.TextField(null=True, blank=True, help_text="Notes from librarian/admin")
    processed_by = models.ForeignKey(UserProfileinfo, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_requests')
    processed_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.book.title} - {self.requester.user.username} ({self.status})"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    class Meta:
        ordering = ['-request_date']
        verbose_name = 'Borrow Request'
        verbose_name_plural = 'Borrow Requests'


class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('cancelled', 'Cancelled'),
    ]
    
    borrowing = models.ForeignKey(Borrower, on_delete=models.CASCADE, related_name='return_requests')
    requester = models.ForeignKey(UserProfileinfo, on_delete=models.CASCADE, related_name='return_requests')
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(null=True, blank=True, help_text="Additional notes from requester")
    admin_notes = models.TextField(null=True, blank=True, help_text="Notes from librarian/admin")
    processed_by = models.ForeignKey(UserProfileinfo, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_return_requests')
    processed_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Return request for {self.borrowing.book.title} by {self.requester.user.username}"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    class Meta:
        ordering = ['-request_date']
        verbose_name = 'Return Request'
        verbose_name_plural = 'Return Requests'


class BookReservation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    user = models.ForeignKey(UserProfileinfo, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateTimeField(auto_now_add=True, db_index=True)
    expiry_date = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.book.title} - {self.user.user.username} ({self.status})"
    
    class Meta:
        ordering = ['-reservation_date']
        unique_together = ['book', 'user', 'status']
        verbose_name = 'Book Reservation'
        verbose_name_plural = 'Book Reservations'


# Theme Models
from django.core.cache import cache
from colorfield.fields import ColorField


class ThemeConfiguration(models.Model):
    """
    Theme configuration model for customizing the library system's appearance.
    Allows administrators to configure colors, backgrounds, and UI elements.
    """
    
    # Theme identification
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Theme name (e.g., 'Default', 'Dark Mode', 'University Blue')"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of this theme"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Set as the active theme for the system"
    )
    
    # Primary Colors
    primary_color = ColorField(
        default='#2563eb',
        help_text="Main brand color used for buttons, links, and accents"
    )
    primary_dark = ColorField(
        default='#1d4ed8',
        help_text="Darker shade of primary color for hover states"
    )
    primary_light = ColorField(
        default='#3b82f6',
        help_text="Lighter shade of primary color for backgrounds"
    )
    
    # Secondary Colors
    secondary_color = ColorField(
        default='#64748b',
        help_text="Secondary color for less prominent elements"
    )
    accent_color = ColorField(
        default='#f59e0b',
        help_text="Accent color for highlights and special elements"
    )
    
    # Status Colors
    success_color = ColorField(
        default='#10b981',
        help_text="Color for success messages and positive actions"
    )
    warning_color = ColorField(
        default='#f59e0b',
        help_text="Color for warning messages and caution states"
    )
    danger_color = ColorField(
        default='#ef4444',
        help_text="Color for error messages and destructive actions"
    )
    info_color = ColorField(
        default='#3b82f6',
        help_text="Color for informational messages"
    )
    
    # Background Colors
    background_primary = ColorField(
        default='#ffffff',
        help_text="Main background color for pages"
    )
    background_secondary = ColorField(
        default='#f8fafc',
        help_text="Secondary background color for sections"
    )
    background_dark = ColorField(
        default='#1e293b',
        help_text="Dark background color for contrast areas"
    )
    
    # Text Colors
    text_primary = ColorField(
        default='#1e293b',
        help_text="Primary text color"
    )
    text_secondary = ColorField(
        default='#64748b',
        help_text="Secondary text color for less important text"
    )
    text_muted = ColorField(
        default='#94a3b8',
        help_text="Muted text color for hints and placeholders"
    )
    text_white = ColorField(
        default='#ffffff',
        help_text="White text color for dark backgrounds"
    )
    
    # Border and Divider Colors
    border_color = ColorField(
        default='#e2e8f0',
        help_text="Color for borders and dividers"
    )
    border_light = ColorField(
        default='#f1f5f9',
        help_text="Light border color"
    )
    border_dark = ColorField(
        default='#cbd5e1',
        help_text="Dark border color"
    )
    
    # Card and Component Colors
    card_background = ColorField(
        default='#ffffff',
        help_text="Background color for cards and components"
    )
    card_border = ColorField(
        default='#e2e8f0',
        help_text="Border color for cards"
    )
    card_shadow = models.CharField(
        max_length=100,
        default='0 4px 6px -1px rgb(0 0 0 / 0.1)',
        help_text="CSS box-shadow value for cards"
    )
    
    # Button Styles
    button_radius = models.CharField(
        max_length=20,
        default='0.5rem',
        help_text="Border radius for buttons (e.g., '0.5rem', '8px')"
    )
    
    # Navigation Colors
    navbar_background = ColorField(
        default='#ffffff',
        help_text="Navigation bar background color"
    )
    navbar_text = ColorField(
        default='#1e293b',
        help_text="Navigation bar text color"
    )
    navbar_hover = ColorField(
        default='#f1f5f9',
        help_text="Navigation bar hover background color"
    )
    
    # Footer Colors
    footer_background = ColorField(
        default='#1e293b',
        help_text="Footer background color"
    )
    footer_text = ColorField(
        default='#94a3b8',
        help_text="Footer text color"
    )
    
    # Book Card Specific Colors
    book_card_background = ColorField(
        default='#ffffff',
        help_text="Background color for book cards"
    )
    book_card_border = ColorField(
        default='#e2e8f0',
        help_text="Border color for book cards"
    )
    book_card_hover = ColorField(
        default='#f8fafc',
        help_text="Hover background color for book cards"
    )
    book_available_color = ColorField(
        default='#10b981',
        help_text="Color indicator for available books"
    )
    book_borrowed_color = ColorField(
        default='#f59e0b',
        help_text="Color indicator for borrowed books"
    )
    book_overdue_color = ColorField(
        default='#ef4444',
        help_text="Color indicator for overdue books"
    )
    
    # Dashboard Colors
    dashboard_card_bg = ColorField(
        default='#ffffff',
        help_text="Dashboard card background color"
    )
    dashboard_stat_primary = ColorField(
        default='#2563eb',
        help_text="Primary dashboard statistic color"
    )
    dashboard_stat_success = ColorField(
        default='#10b981',
        help_text="Success dashboard statistic color"
    )
    dashboard_stat_warning = ColorField(
        default='#f59e0b',
        help_text="Warning dashboard statistic color"
    )
    dashboard_stat_danger = ColorField(
        default='#ef4444',
        help_text="Danger dashboard statistic color"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Theme Configuration"
        verbose_name_plural = "Theme Configurations"
        ordering = ['-is_active', 'name']
    
    def __str__(self):
        status = " (Active)" if self.is_active else ""
        return f"{self.name}{status}"
    
    def save(self, *args, **kwargs):
        # Ensure only one theme is active at a time
        if self.is_active:
            ThemeConfiguration.objects.filter(is_active=True).update(is_active=False)
        
        super().save(*args, **kwargs)
        
        # Clear theme cache when theme is updated
        cache.delete('active_theme')
        cache.delete(f'theme_{self.id}')
    
    @classmethod
    def get_active_theme(cls):
        """Get the currently active theme configuration."""
        # Try to get from cache first
        theme = cache.get('active_theme')
        if theme is None:
            try:
                theme = cls.objects.get(is_active=True)
                cache.set('active_theme', theme, 3600)  # Cache for 1 hour
            except cls.DoesNotExist:
                # Create default theme if none exists
                theme = cls.objects.create(
                    name="Default Theme",
                    description="Default library system theme",
                    is_active=True
                )
        return theme
    
    def to_css_variables(self):
        """Convert theme colors to CSS custom properties."""
        return {
            '--primary-color': self.primary_color,
            '--primary-dark': self.primary_dark,
            '--primary-light': self.primary_light,
            '--secondary-color': self.secondary_color,
            '--accent-color': self.accent_color,
            '--success-color': self.success_color,
            '--warning-color': self.warning_color,
            '--danger-color': self.danger_color,
            '--info-color': self.info_color,
            '--background-primary': self.background_primary,
            '--background-secondary': self.background_secondary,
            '--background-dark': self.background_dark,
            '--text-primary': self.text_primary,
            '--text-secondary': self.text_secondary,
            '--text-muted': self.text_muted,
            '--text-white': self.text_white,
            '--border-color': self.border_color,
            '--border-light': self.border_light,
            '--border-dark': self.border_dark,
            '--card-background': self.card_background,
            '--card-border': self.card_border,
            '--card-shadow': self.card_shadow,
            '--button-radius': self.button_radius,
            '--navbar-background': self.navbar_background,
            '--navbar-text': self.navbar_text,
            '--navbar-hover': self.navbar_hover,
            '--footer-background': self.footer_background,
            '--footer-text': self.footer_text,
            '--book-card-background': self.book_card_background,
            '--book-card-border': self.book_card_border,
            '--book-card-hover': self.book_card_hover,
            '--book-available-color': self.book_available_color,
            '--book-borrowed-color': self.book_borrowed_color,
            '--book-overdue-color': self.book_overdue_color,
            '--dashboard-card-bg': self.dashboard_card_bg,
            '--dashboard-stat-primary': self.dashboard_stat_primary,
            '--dashboard-stat-success': self.dashboard_stat_success,
            '--dashboard-stat-warning': self.dashboard_stat_warning,
            '--dashboard-stat-danger': self.dashboard_stat_danger,
        }
    
    def generate_css(self):
        """Generate CSS string with theme variables."""
        variables = self.to_css_variables()
        css_vars = '\n'.join([f'    {key}: {value};' for key, value in variables.items()])
        
        return f"""
/* Auto-generated theme CSS */
:root {{
{css_vars}
}}

/* Theme-specific component styles */
.btn-primary {{
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}}

.btn-primary:hover {{
    background-color: var(--primary-dark);
    border-color: var(--primary-dark);
}}

.btn-secondary {{
    background-color: var(--secondary-color);
    border-color: var(--secondary-color);
}}

.btn-success {{
    background-color: var(--success-color);
    border-color: var(--success-color);
}}

.btn-warning {{
    background-color: var(--warning-color);
    border-color: var(--warning-color);
}}

.btn-danger {{
    background-color: var(--danger-color);
    border-color: var(--danger-color);
}}

.card {{
    background-color: var(--card-background);
    border-color: var(--card-border);
    box-shadow: var(--card-shadow);
}}

.navbar {{
    background-color: var(--navbar-background) !important;
    color: var(--navbar-text);
}}

.navbar .nav-link {{
    color: var(--navbar-text) !important;
}}

.navbar .nav-link:hover {{
    background-color: var(--navbar-hover);
}}

.book-card {{
    background-color: var(--book-card-background);
    border-color: var(--book-card-border);
}}

.book-card:hover {{
    background-color: var(--book-card-hover);
}}

.book-status.available {{
    color: var(--book-available-color);
}}

.book-status.borrowed {{
    color: var(--book-borrowed-color);
}}

.book-status.overdue {{
    color: var(--book-overdue-color);
}}

.dashboard-card {{
    background-color: var(--dashboard-card-bg);
}}

.stat-primary {{
    color: var(--dashboard-stat-primary);
}}

.stat-success {{
    color: var(--dashboard-stat-success);
}}

.stat-warning {{
    color: var(--dashboard-stat-warning);
}}

.stat-danger {{
    color: var(--dashboard-stat-danger);
}}
"""


class ThemePreset(models.Model):
    """Predefined theme presets for quick setup."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    theme_data = models.JSONField(
        help_text="JSON data containing all theme color values"
    )
    preview_image = models.ImageField(
        upload_to='theme_previews/',
        blank=True,
        null=True,
        help_text="Preview image of this theme"
    )
    is_built_in = models.BooleanField(
        default=False,
        help_text="Built-in themes cannot be deleted"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Theme Preset"
        verbose_name_plural = "Theme Presets"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def apply_to_theme(self, theme_config):
        """Apply this preset to a theme configuration."""
        for field, value in self.theme_data.items():
            if hasattr(theme_config, field):
                setattr(theme_config, field, value)
        return theme_config