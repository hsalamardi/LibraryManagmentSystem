from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import Book, Borrower, BorrowRequest
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone


# Register your models here.


class BookResource(resources.ModelResource):

    class Meta:
        model = Book

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
