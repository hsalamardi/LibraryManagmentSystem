from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import Book, Borrower, BorrowRequest, ReturnRequest
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone


# Register your models here.


class BookResource(resources.ModelResource):
    
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
        if 'Place_of_Publication' in row:
            row['place_of_publication'] = clean_value(row['Place_of_Publication'])
        if 'website' in row:
            row['website'] = clean_value(row['website'])
        if 'Source' in row:
            row['source'] = clean_value(row['Source'])
        if 'Cover_Type' in row:
            cover_type = clean_value(row['Cover_Type'])
            # Map to our choices
            if cover_type:
                cover_lower = cover_type.lower()
                if 'hard' in cover_lower:
                    row['cover_type'] = 'hardcover'
                elif 'paper' in cover_lower or 'soft' in cover_lower:
                    row['cover_type'] = 'paperback'
                elif 'spiral' in cover_lower:
                    row['cover_type'] = 'spiral'
                elif 'digital' in cover_lower:
                    row['cover_type'] = 'digital'
                else:
                    row['cover_type'] = 'paperback'  # Default
            else:
                row['cover_type'] = 'paperback'
        if 'Condition' in row:
            condition = clean_value(row['Condition'])
            # Map to our choices
            if condition:
                condition_lower = condition.lower()
                if 'excellent' in condition_lower:
                    row['condition'] = 'excellent'
                elif 'good' in condition_lower:
                    row['condition'] = 'good'
                elif 'fair' in condition_lower:
                    row['condition'] = 'fair'
                elif 'poor' in condition_lower:
                    row['condition'] = 'poor'
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
        if 'Publication_Datte' in row:
            # Handle the typo in the Excel file
            row['publication_date'] = clean_date(row['Publication_Datte'])
        
        # Handle serial and shelf
        if 'serial' in row:
            row['serial'] = str(row['serial']) if row['serial'] and not pd.isna(row['serial']) else ''
        if 'shelf' in row:
            row['shelf'] = str(row['shelf']) if row['shelf'] and not pd.isna(row['shelf']) else ''
            
        # Set default values for required fields
        if not row.get('title') or row.get('title') == 'None':
            row['title'] = 'Unknown Title'
        if not row.get('author') or row.get('author') == 'None':
            row['author'] = 'Unknown Author'
            
        # Ensure serial is unique and not empty
        if not row.get('serial') or row.get('serial') == 'None':
            import time
            row['serial'] = f"AUTO_{int(time.time())}_{row.get('title', 'book')[:10]}"
            
        return row
    
    class Meta:
        model = Book
        import_id_fields = ('serial',)
        fields = (
            'serial', 'shelf', 'title', 'author', 'isbn', 'publisher',
            'publication_date', 'edition', 'pages', 'language', 'dewey_code',
            'main_class', 'divisions', 'sections', 'cutter_author', 'volume',
            'series', 'editor', 'translator', 'place_of_publication', 'website',
            'source', 'cover_type', 'condition', 'copy_number', 'book_summary',
            'contents', 'keywords'
        )
        skip_unchanged = True
        report_skipped = True

class BookAdmin(ImportExportModelAdmin):
    resource_class = BookResource
    list_display = ['title', 'author', 'isbn', 'barcode', 'is_available', 'date_added']
    list_filter = ['is_available', 'language', 'condition', 'date_added']
    search_fields = ['title', 'author', 'isbn', 'barcode', 'keywords']
    readonly_fields = ['date_added', 'last_updated']
    fieldsets = (
        ('Basic Information', {
            'fields': ('serial', 'shelf', 'title', 'author', 'isbn', 'barcode')
        }),
        ('Publication Details', {
            'fields': ('publisher', 'publication_date', 'edition', 'pages', 'language')
        }),
        ('Classification', {
            'fields': ('dewey_code', 'main_class', 'divisions', 'sections', 'cutter_author')
        }),
        ('Additional Information', {
            'fields': ('volume', 'series', 'editor', 'translator', 'place_of_publication', 'website', 'source')
        }),
        ('Physical Details', {
            'fields': ('cover_type', 'condition', 'copy_number', 'cover_image')
        }),
        ('Content', {
            'fields': ('book_summary', 'contents', 'keywords')
        }),
        ('Status', {
            'fields': ('is_available', 'date_added', 'last_updated')
        }),
    )

admin.site.register(Book, BookAdmin)

class BorrowerResource(resources.ModelResource):

    class Meta:
        model = Borrower

class BorrowerAdmin(ImportExportModelAdmin):
    resource_class = BorrowerResource
    list_display = ['book', 'borrower', 'borrow_date', 'due_date', 'status', 'fine_amount']
    list_filter = ['status', 'borrow_date', 'due_date']
    search_fields = ['book__title', 'borrower__user__username', 'borrower__user__email']
    readonly_fields = ['borrow_date']

admin.site.register(Borrower, BorrowerAdmin)


class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = ['book', 'requester', 'request_date', 'requested_duration_days', 'status', 'processed_by', 'action_buttons']
    list_filter = ['status', 'request_date', 'processed_date']
    search_fields = ['book__title', 'requester__user__username', 'requester__user__email']
    readonly_fields = ['request_date', 'processed_date']
    fieldsets = (
        ('Request Information', {
            'fields': ('book', 'requester', 'request_date', 'requested_duration_days', 'notes')
        }),
        ('Status', {
            'fields': ('status', 'admin_notes', 'processed_by', 'processed_date')
        }),
    )
    
    def action_buttons(self, obj):
        if obj.status == 'pending':
            approve_url = reverse('admin:approve_borrow_request', args=[obj.pk])
            deny_url = reverse('admin:deny_borrow_request', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Approve</a>&nbsp;'
                '<a class="button" href="{}">Deny</a>',
                approve_url, deny_url
            )
        return f"Status: {obj.get_status_display()}"
    action_buttons.short_description = 'Actions'
    action_buttons.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            obj.processed_by = request.user.userprofileinfo
            obj.processed_date = timezone.now()
        super().save_model(request, obj, form, change)

admin.site.register(BorrowRequest, BorrowRequestAdmin)


class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ['borrowing', 'requester', 'request_date', 'status', 'processed_by', 'action_buttons']
    list_filter = ['status', 'request_date', 'processed_date']
    search_fields = ['borrowing__book__title', 'requester__user__username', 'requester__user__email']
    readonly_fields = ['request_date', 'processed_date']
    fieldsets = (
        ('Request Information', {
            'fields': ('borrowing', 'requester', 'request_date', 'notes')
        }),
        ('Status', {
            'fields': ('status', 'admin_notes', 'processed_by', 'processed_date')
        }),
    )
    
    def action_buttons(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="/return-requests/{}/approve/">Approve</a>&nbsp;'
                '<a class="button" href="/return-requests/{}/deny/">Deny</a>',
                obj.pk, obj.pk
            )
        return '-'
    action_buttons.short_description = 'Actions'
    action_buttons.allow_tags = True


admin.site.register(ReturnRequest, ReturnRequestAdmin)
