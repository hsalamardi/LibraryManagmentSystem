from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import Book, Borrower, BorrowRequest, ReturnRequest, ThemeConfiguration, ThemePreset, Category
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone


# Register your models here.


class BookResource(resources.ModelResource):

    def get_instance(self, instance_loader, row):
        # Attempt to find an existing book by serial number
        try:
            return self.Meta.model.objects.get(serial=row.get('serial'))
        except self.Meta.model.DoesNotExist:
            return None

    class Meta:
        model = Book
        fields = (
            'id', 'title', 'author', 'isbn', 'publisher', 'edition', 'pages', 'language', 'dewey_code',
            'main_class', 'divisions', 'sections', 'cutter_author', 'volume', 'series', 'editor',
            'translator', 'publication_date', 'book_summary', 'contents', 'keywords', 'serial',
            'condition', 'copy_number', 'is_available', 'status', 'website', 'place_of_publication', 'source', 'cover_type',
            'borrow_date', 'return_date', 'borrower',
            'is_approved', 'approved_by', 'approved_date', 'is_returned', 'returned_by',
            'returned_date', 'is_lost', 'lost_date', 'lost_by', 'is_damaged', 'damaged_date',
            'damaged_by', 'is_reserved', 'reserved_by', 'is_hidden',
            'hidden_date', 'hidden_by', 'created_at', 'updated_at'
        )
        exclude = ('category',)
        export_order = fields
        import_id_fields = ('serial',)

    def before_import_row(self, row, **kwargs):
        """Clean and map data before importing"""
        import pandas as pd
        from datetime import datetime
        
        def clean_value(value):
            """Clean individual values, handling NaN and empty strings"""
            if pd.isna(value) or value == 'NaN' or str(value).strip() == '':
                return None
            return str(value).strip()
        
        def clean_numeric(value):
            """Clean numeric values, handling NaN"""
            if pd.isna(value) or value == 'NaN' or str(value).strip() == '':
                return None
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return None
        
        def clean_date(value):
            """Clean date values, handling various formats"""
            if pd.isna(value) or value == 'NaN' or str(value).strip() == '':
                return None
            try:
                # Try to parse various date formats
                date_str = str(value).strip()
                if len(date_str) == 4 and date_str.isdigit():  # Just year
                    return f"{date_str}-01-01"
                return date_str
            except:
                return None
        
        # Map Excel columns to model fields with cleaning
        if 'Title' in row:
            row['title'] = clean_value(row['Title'])
        if 'Author' in row:
            row['author'] = clean_value(row['Author'])
        if 'ISBN' in row:
            row['isbn'] = clean_value(row['ISBN'])
        if 'Publisher' in row:
            row['publisher'] = clean_value(row['Publisher'])
        if 'Edition' in row:
            row['edition'] = clean_value(row['Edition'])
        if 'Pages' in row:
            row['pages'] = clean_numeric(row['Pages'])
        if 'Language' in row:
            language = clean_value(row['Language'])
            # Map common language values to our choices
            if language:
                language_lower = language.lower()
                if 'english' in language_lower or 'en' == language_lower:
                    row['language'] = 'en'
                elif 'arabic' in language_lower or 'ar' == language_lower:
                    row['language'] = 'ar'
                elif 'french' in language_lower or 'fr' == language_lower:
                    row['language'] = 'fr'
                elif 'spanish' in language_lower or 'es' == language_lower:
                    row['language'] = 'es'
                elif 'german' in language_lower or 'de' == language_lower:
                    row['language'] = 'de'
                else:
                    row['language'] = 'other'
            else:
                row['language'] = 'en'  # Default to English
        if 'Dewey_Code' in row:
            row['dewey_code'] = clean_value(row['Dewey_Code'])
        if 'Main_Class' in row:
            row['main_class'] = clean_value(row['Main_Class'])
        if 'Divisions' in row:
            row['divisions'] = clean_value(row['Divisions'])
        if 'Sections' in row:
            row['sections'] = clean_value(row['Sections'])
        if 'Cutter_Author' in row:
            row['cutter_author'] = clean_value(row['Cutter_Author'])
        if 'Volume' in row:
            row['volume'] = clean_value(row['Volume'])
        if 'Series' in row:
            row['series'] = clean_value(row['Series'])
        if 'Editor' in row:
            row['editor'] = clean_value(row['Editor'])
        if 'Translator' in row:
            row['translator'] = clean_value(row['Translator'])
        if 'Publication_Date' in row:
            row['publication_date'] = clean_date(row['Publication_Date'])
        if 'Condition' in row:
            condition = clean_value(row['Condition'])
            if condition:
                condition_lower = condition.lower()
                if 'new' in condition_lower:
                    row['condition'] = 'new'
                elif 'used' in condition_lower:
                    row['condition'] = 'used'
                elif 'damaged' in condition_lower:
                    row['condition'] = 'damaged'
                else:
                    row['condition'] = 'good'  # Default
            else:
                row['condition'] = 'good'
        if 'Copy' in row:
            row['copy_number'] = clean_numeric(row['Copy']) or 1
        if 'Book_Summary' in row:
            row['book_summary'] = clean_value(row['Book_Summary'])
        if 'Contents' in row:
            row['contents'] = clean_value(row['Contents'])
        if 'Keywords' in row:
            row['keywords'] = clean_value(row['Keywords'])
        if 'Category' in row:
            category_name = clean_value(row['Category'])
            if category_name:
                category, created = Category.objects.get_or_create(name=category_name)
                row['category'] = category.id
            else:
                row['category'] = None
        if 'Publication_Datte' in row:
            # Handle the typo in the Excel file
            row['publication_date'] = clean_date(row['Publication_Datte'])
        
        # Set default values for fields not present in the Excel file
        if 'status' not in row:
            row['status'] = 'available'
        if 'borrow_date' not in row:
            row['borrow_date'] = None
        if 'return_date' not in row:
            row['return_date'] = None
        if 'borrower' not in row:
            row['borrower'] = None
        if 'is_approved' not in row:
            row['is_approved'] = False
        if 'approved_by' not in row:
            row['approved_by'] = None
        if 'approved_date' not in row:
            row['approved_date'] = None
        if 'is_returned' not in row:
            row['is_returned'] = False
        if 'returned_by' not in row:
            row['returned_by'] = None
        if 'returned_date' not in row:
            row['returned_date'] = None
        if 'is_lost' not in row:
            row['is_lost'] = False
        if 'lost_date' not in row:
            row['lost_date'] = None
        if 'lost_by' not in row:
            row['lost_by'] = None
        if 'is_damaged' not in row:
            row['is_damaged'] = False
        if 'damaged_date' not in row:
            row['damaged_date'] = None
        if 'damaged_by' not in row:
            row['damaged_by'] = None
        if 'is_reserved' not in row:
            row['is_reserved'] = False
        if 'reserved_date' not in row:
            row['reserved_date'] = None
        if 'reserved_by' not in row:
            row['reserved_by'] = None
        if 'is_hidden' not in row:
            row['is_hidden'] = False
        if 'hidden_date' not in row:
            row['hidden_date'] = None
        if 'hidden_by' not in row:
            row['hidden_by'] = None
        if 'created_at' not in row:
            row['created_at'] = timezone.now()
        if 'updated_at' not in row:
            row['updated_at'] = timezone.now()

        return row


@admin.register(Book)
class BookAdmin(ImportExportModelAdmin):
    resource_class = BookResource
    list_display = (
        'title', 'author', 'isbn', 'category', 'language', 'is_available', 'date_added', 'last_updated'
    )
    list_filter = (
        'category', 'language', 'is_available', 'date_added', 'last_updated'
    )
    search_fields = ('title', 'author', 'isbn', 'category__name')
    actions = ['make_available', 'make_lost', 'make_damaged', 'make_hidden']

    def make_available(self, request, queryset):
        queryset.update(is_available=True)

    make_available.short_description = "Mark selected books as available"

    def make_lost(self, request, queryset):
        queryset.update(is_available=False) # Assuming lost means not available

    make_lost.short_description = "Mark selected books as lost"

    def make_damaged(self, request, queryset):
        queryset.update(is_available=False) # Assuming damaged means not available

    make_damaged.short_description = "Mark selected books as damaged"

    def make_hidden(self, request, queryset):
        queryset.update(is_available=False) # Assuming hidden means not available

    make_hidden.short_description = "Mark selected books as hidden"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Borrower)
class BorrowerAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower', 'borrow_date', 'due_date', 'status', 'fine_amount')
    list_filter = ('status', 'borrow_date', 'due_date')
    search_fields = ('book__title', 'borrower__user__username')


@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = ('book', 'requester', 'request_date', 'status', 'processed_date')
    list_filter = ('status', 'request_date')
    search_fields = ('book__title', 'requester__user__username')


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('borrowing', 'requester', 'request_date', 'status', 'processed_date')
    list_filter = ('status', 'request_date')
    search_fields = ('borrowing__book__title', 'requester__user__username')


# Admin site customizations
admin.site.site_header = "Library Management System Admin"
admin.site.site_title = "LMS Admin Portal"
admin.site.index_title = "Welcome to LMS Admin"
