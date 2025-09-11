from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import CommandError
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser from environment variables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if user already exists (will update existing user)',
        )

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not username:
            raise CommandError('DJANGO_SUPERUSER_USERNAME environment variable is required')
        if not email:
            raise CommandError('DJANGO_SUPERUSER_EMAIL environment variable is required')
        if not password:
            raise CommandError('DJANGO_SUPERUSER_PASSWORD environment variable is required')

        # Check if user already exists
        try:
            user = User.objects.get(username=username)
            if options['force']:
                user.email = email
                user.set_password(password)
                user.is_staff = True
                user.is_superuser = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated superuser "{username}"')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'User "{username}" already exists. Use --force to update.'
                    )
                )
                return
        except User.DoesNotExist:
            # Create new superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser "{username}"')
            )

        # Display login information
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('DJANGO ADMIN LOGIN CREDENTIALS:'))
        self.stdout.write('='*50)
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Admin URL: http://127.0.0.1:8000/admin/')
        self.stdout.write('='*50 + '\n')