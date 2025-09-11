from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import UserProfileinfo
from .models import  Contact
from .models import UserProfileinfo
from import_export import resources
# Register your models here.

class UserProfileinfoResource(resources.ModelResource):

    class Meta:
        model = UserProfileinfo
class UserProfileinfoAdmin(ImportExportModelAdmin):
    resource_class = UserProfileinfoResource
admin.site.register(UserProfileinfo, UserProfileinfoAdmin)




class ContactResource(resources.ModelResource):

    class Meta:
        model = Contact
class ContactAdmin(ImportExportModelAdmin):
    resource_class = ContactResource
admin.site.register(Contact, ContactAdmin)

