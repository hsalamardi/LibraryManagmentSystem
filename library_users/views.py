from urllib.request import HTTPRedirectHandler
from . import forms
from django.shortcuts import render, redirect, reverse
from django.http import Http404, HttpResponseForbidden
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.views.generic.edit import FormMixin
from .forms  import UserForm, UserProfileinfoForm, ContactForm
from .models import Contact
from django.urls import reverse,resolve
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.http import HttpRequest, HttpResponse,HttpResponseRedirect

import library_users

# Create your views here.

def the_index(request):
    mydect2 = {'name2':'This is yje index page of Library users app !!  '}
    return render(request, "library_users/index.html",context=mydect2)


def register(request):
    registered = False
    if request.method == "POST":
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileinfoForm(data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'profile_image' in request.FILES:
                profile.profile_image = request.FILES['profile_pic']
            profile.save()

            registered = True
        else:
            print(user_form.errors,profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = UserProfileinfoForm()

    return render(request, "library_users/registration.html",context=
                                        {'registered':registered,'user_form': user_form, 'profile_form': profile_form})

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('books:landing'))

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username,password=password)     

        if user:
                if user.is_active:
                    login(request,user)
                    return HttpResponseRedirect(reverse('books:view_books_list'))
                else:
                    return HttpResponse("Account Not Active")
        else:
                print("someone tried to ogin and failled")         
                return HttpResponse('invalid username supplied')
    else:
        return render(request,"library_users/login.html",{})    



def contacts(request):
    
    contacts_view = Contact.objects.all()
    contacts_dict= {'contact_key': contacts_view}
    return render(request, "library_users/contact.html",context=contacts_dict)
#@login_required(login_url='/library_users/register')
#def contact_form(request):
#    form = forms.ContactForm()
#    if request.method == "GET":
#        form = ContactForm(request.GET)
#        if form.is_valid():
#            form.save(commit=True)
#            return contacts(request)
#        else:
#            
#            print(form.errors)

#    return render(request, "library_users/contact.html",context={'form':form})
def contact_form(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            new_message = Contact()
            new_message.name = name
            new_message.email = email
            new_message.message = message
            new_message.save()
            messages.success(request, "Your message is sent")
            return contacts(request)
    if request.user.is_authenticated:
        form = ContactForm()
        form.fields['name'].initial = request.user.username
        form.fields['email'].initial = request.user.email
        form.fields['message'].widget.attrs['placeholder'] = 'Write your message here'
        form.fields['name'].label = 'Login'
        form.fields['name'].widget.attrs['readonly'] = True
        form.fields['email'].widget.attrs['readonly'] = True
        return render(request, 'library_users/contact.html', {'form': form})
    else:
        form = ContactForm()
        form.fields['name'].widget.attrs['placeholder'] = 'Your name'
        form.fields['email'].widget.attrs['placeholder'] = 'Your email'
        form.fields['message'].widget.attrs['placeholder'] = 'Write your message here'
        return render(request, 'library_users/contact.html', {'form': form})
