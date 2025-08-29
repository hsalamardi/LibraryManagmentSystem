from django import forms
from django.contrib.auth.models import User
from .models import UserProfileinfo, Contact

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ('first_name','last_name','username','email','password')

class UserProfileinfoForm(forms.ModelForm):
        class Meta:
            model = UserProfileinfo
            fields = ('department','profile_image')


class ContactForm(forms.ModelForm):
    name = forms.CharField(label='Name')
    email = forms.EmailField(label='E-mail')
    message = forms.CharField(label='Message', widget=forms.Textarea())

    class Meta():
        model = Contact
        fields = '__all__'



