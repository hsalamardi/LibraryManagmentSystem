from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import Book
from .models import  Borrower
from import_export.admin import ImportExportModelAdmin
from import_export import resources


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
admin.site.register(Borrower, BorrowerAdmin )
