from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import Book, Borrower, BookReservation
from library_users.models import UserProfileinfo


class NewBook_form(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'serial', 'shelf', 'title', 'isbn', 'barcode', 'author', 'publisher',
            'publication_date', 'edition', 'pages', 'language', 'dewey_code',
            'volume', 'series', 'editor', 'translator', 'place_of_publication',
            'website', 'source', 'cover_type', 'condition', 'copy_number',
            'cover_image', 'book_summary', 'contents', 'keywords'
        ]
        widgets = {
            'publication_date': forms.DateInput(attrs={'type': 'date'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scan or enter barcode', 'id': 'barcode-input'}),
            'cover_image': forms.ClearableFileInput(attrs={'accept': 'image/*', 'class': 'form-control'}),
            'book_summary': forms.Textarea(attrs={'rows': 4}),
            'contents': forms.Textarea(attrs={'rows': 4}),
            'keywords': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter keywords separated by commas'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://example.com'}),
        }
    
    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn')
        if isbn:
            # Remove any hyphens or spaces
            isbn = isbn.replace('-', '').replace(' ', '')
            if len(isbn) not in [10, 13]:
                raise ValidationError('ISBN must be 10 or 13 digits long.')
        return isbn
    
    def clean_publication_date(self):
        pub_date = self.cleaned_data.get('publication_date')
        if pub_date and pub_date > date.today():
            raise ValidationError('Publication date cannot be in the future.')
        return pub_date
    
    def clean_barcode(self):
        barcode = self.cleaned_data.get('barcode')
        if barcode:
            # Remove any spaces or special characters
            barcode = ''.join(filter(str.isalnum, barcode))
            if len(barcode) < 8:
                raise ValidationError('Barcode must be at least 8 characters long.')
            if len(barcode) > 50:
                raise ValidationError('Barcode cannot exceed 50 characters.')
        return barcode
    
    def clean_cover_image(self):
        cover_image = self.cleaned_data.get('cover_image')
        if cover_image:
            # Check file size (max 5MB)
            if cover_image.size > 5 * 1024 * 1024:
                raise ValidationError('Image file size must be less than 5MB.')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if cover_image.content_type not in allowed_types:
                raise ValidationError('Only JPEG, PNG, GIF, and WebP images are allowed.')
        
        return cover_image


class NewBorrower_form(forms.ModelForm):
    class Meta:
        model = Borrower
        fields = ['book', 'borrower', 'due_date', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show available books
        self.fields['book'].queryset = Book.objects.filter(is_available=True)
        # Only show active users
        self.fields['borrower'].queryset = UserProfileinfo.objects.filter(status='active')
        # Set default due date to 2 weeks from today
        self.fields['due_date'].initial = date.today() + timedelta(days=14)
    
    def clean(self):
        cleaned_data = super().clean()
        book = cleaned_data.get('book')
        borrower = cleaned_data.get('borrower')
        
        if book and not book.is_available:
            raise ValidationError('This book is not available for borrowing.')
        
        if borrower and not borrower.can_borrow_books:
            raise ValidationError('This user cannot borrow books at this time.')
        
        return cleaned_data


class BookSearchForm(forms.Form):
    q = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by title, author, ISBN, barcode, or keywords...',
            'class': 'form-control'
        })
    )
    availability = forms.ChoiceField(
        choices=[('', 'All'), ('available', 'Available'), ('borrowed', 'Borrowed')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    language = forms.ChoiceField(
        choices=[('', 'All Languages')] + Book.LANGUAGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class BookReservationForm(forms.ModelForm):
    class Meta:
        model = BookReservation
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional notes...'}),
        }


class ReturnBookForm(forms.Form):
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Optional return notes (condition, issues, etc.)...'
        })
    )


class BarcodeScanForm(forms.Form):
    barcode = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Scan or enter barcode',
            'id': 'barcode-scan-input',
            'autocomplete': 'off'
        })
    )
    
    def clean_barcode(self):
        barcode = self.cleaned_data.get('barcode')
        if barcode:
            # Remove any spaces or special characters
            barcode = ''.join(filter(str.isalnum, barcode))
            if len(barcode) < 8:
                raise ValidationError('Barcode must be at least 8 characters long.')
        return barcode

