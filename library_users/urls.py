from urllib.parse import urlparse
from django.urls import path
from . import views
from .views import (
    contact_form,
)

app_name= 'library_users'
urlpatterns = [
    path('library_users/', views.the_index,name='index'),
    path('library_users/register/', views.register,name='register'),
    path('library_users/login/', view=views.user_login, name='login'),
    path('library_users/logout/', view=views.user_logout, name='logout'),
    path('library_users/contact/', view=views.contact_form, name='contact'),
    path('library_users/profile/', views.user_profile, name='profile'),

]