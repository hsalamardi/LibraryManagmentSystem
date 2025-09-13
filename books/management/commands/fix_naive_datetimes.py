from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from books.models import Book

class Command(BaseCommand):
    help = 'Fixes naive datetimes in Book.date_added and User.date_joined fields by converting them to timezone-aware datetimes.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to fix naive datetimes...'))

        User = get_user_model()

        # Fix Book.date_added
        self.stdout.write('Processing Book.date_added...')
        for book in Book.objects.all():
            if timezone.is_naive(book.date_added):
                book.date_added = timezone.make_aware(book.date_added, timezone.get_current_timezone())
                book.save(update_fields=['date_added'])
                self.stdout.write(self.style.WARNING(f'Fixed naive date_added for Book ID: {book.id}'))
        self.stdout.write(self.style.SUCCESS('Finished processing Book.date_added.'))

        # Fix User.date_joined
        self.stdout.write('Processing User.date_joined...')
        for user in User.objects.all():
            if timezone.is_naive(user.date_joined):
                user.date_joined = timezone.make_aware(user.date_joined, timezone.get_current_timezone())
                user.save(update_fields=['date_joined'])
                self.stdout.write(self.style.WARNING(f'Fixed naive date_joined for User ID: {user.id}'))
        self.stdout.write(self.style.SUCCESS('Finished processing User.date_joined.'))

        self.stdout.write(self.style.SUCCESS('Naive datetime fixing process completed.'))