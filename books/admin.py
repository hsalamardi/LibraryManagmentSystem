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
admin.site.register(Book, BookAdmin)

class BorrowerResource(resources.ModelResource):

    class Meta:
        model = Borrower

class BorrowerAdmin(ImportExportModelAdmin):
    resource_class = BorrowerResource
admin.site.register(Borrower, BorrowerAdmin )
