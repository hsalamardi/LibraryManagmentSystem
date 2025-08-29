from cProfile import label
from django import forms
from django.db import models
from enum import unique
from unittest.util import _MAX_LENGTH
from library_users.models import UserProfileinfo

# Create your models here.

class Book(models.Model):
    name = models.CharField(max_length=100,unique=False)
    auther = models.CharField(max_length=56,unique=False)
    type = models.CharField(max_length=56,unique=False)
    isbn = models.PositiveBigIntegerField(unique=False)
    copies =  models.PositiveSmallIntegerField(unique=False)
    issue_date = models.DateField(help_text='Date format MM-DD-YYYY')
    out = models.BooleanField(blank = True)


    def __str__(self):
        return self.name

#class UserProfileinfo(models.Model):
#    def __str__(self):
#        return self.name

class Borrower(models.Model):
    borrower_book = models.ForeignKey(Book,on_delete=models.CASCADE,related_name='book_borrower')
    borrower_name = models.OneToOneField(UserProfileinfo,default='1',on_delete=models.CASCADE,related_name='borrower_name')
    department = models.CharField(max_length=56,unique=False)
    borrow_date = models.DateField()
    return_date = models.DateField()


    
    blacklisted = models.BooleanField()
    
    def __str__(self):
        return self.borrower_book