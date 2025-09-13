from urllib.parse import urlparse
from django.urls import path
from . import views
from .views import (
    contact_form,
)

app_name= 'library_users'
urlpatterns = [
    path('', views.the_index,name='index'),
    path('register/', views.register,name='register'),
    path('login/', view=views.user_login, name='login'),
    path('logout/', view=views.user_logout, name='logout'),
    path('contact/', view=views.contact_form, name='contact'),
    path('profile/', views.user_profile, name='profile'),

]