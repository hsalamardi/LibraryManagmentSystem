from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from books.models import Book, Borrower, BookReservation
from library_users.models import UserProfileinfo, Contact, InboxMessages


class Command(BaseCommand):
    help = 'Create user groups and assign permissions for the library system'

    def handle(self, *args, **options):
        # Create groups
        librarian_group, created = Group.objects.get_or_create(name='Librarian')
        member_group, created = Group.objects.get_or_create(name='Member')
        admin_group, created = Group.objects.get_or_create(name='Library Admin')

        # Get content types
        book_ct = ContentType.objects.get_for_model(Book)
        borrower_ct = ContentType.objects.get_for_model(Borrower)
        reservation_ct = ContentType.objects.get_for_model(BookReservation)
        profile_ct = ContentType.objects.get_for_model(UserProfileinfo)
        contact_ct = ContentType.objects.get_for_model(Contact)
        inbox_ct = ContentType.objects.get_for_model(InboxMessages)

        # Define permissions for each group
        
        # Member permissions (basic users)
        member_permissions = [
            # Books - can view only
            Permission.objects.get(codename='view_book', content_type=book_ct),
            # Can view their own borrowings
            Permission.objects.get(codename='view_borrower', content_type=borrower_ct),
            # Can create reservations
            Permission.objects.get(codename='add_bookreservation', content_type=reservation_ct),
            Permission.objects.get(codename='view_bookreservation', content_type=reservation_ct),
            # Can view and change their own profile
            Permission.objects.get(codename='view_userprofileinfo', content_type=profile_ct),
            Permission.objects.get(codename='change_userprofileinfo', content_type=profile_ct),
            # Can create contact messages
            Permission.objects.get(codename='add_contact', content_type=contact_ct),
            # Can view their inbox
            Permission.objects.get(codename='view_inboxmessages', content_type=inbox_ct),
        ]

        # Librarian permissions (staff members)
        librarian_permissions = member_permissions + [
            # Books - full CRUD
            Permission.objects.get(codename='add_book', content_type=book_ct),
            Permission.objects.get(codename='change_book', content_type=book_ct),
            Permission.objects.get(codename='delete_book', content_type=book_ct),
            # Borrowings - full CRUD
            Permission.objects.get(codename='add_borrower', content_type=borrower_ct),
            Permission.objects.get(codename='change_borrower', content_type=borrower_ct),
            Permission.objects.get(codename='delete_borrower', content_type=borrower_ct),
            # Reservations - full CRUD
            Permission.objects.get(codename='change_bookreservation', content_type=reservation_ct),
            Permission.objects.get(codename='delete_bookreservation', content_type=reservation_ct),
            # Can view all user profiles
            Permission.objects.get(codename='view_userprofileinfo', content_type=profile_ct),
            # Can manage contact messages
            Permission.objects.get(codename='view_contact', content_type=contact_ct),
            Permission.objects.get(codename='change_contact', content_type=contact_ct),
            # Can send inbox messages
            Permission.objects.get(codename='add_inboxmessages', content_type=inbox_ct),
            Permission.objects.get(codename='change_inboxmessages', content_type=inbox_ct),
        ]

        # Admin permissions (full access)
        admin_permissions = librarian_permissions + [
            # User profiles - full CRUD
            Permission.objects.get(codename='add_userprofileinfo', content_type=profile_ct),
            Permission.objects.get(codename='change_userprofileinfo', content_type=profile_ct),
            Permission.objects.get(codename='delete_userprofileinfo', content_type=profile_ct),
            # Contact messages - full CRUD
            Permission.objects.get(codename='delete_contact', content_type=contact_ct),
            # Inbox messages - full CRUD
            Permission.objects.get(codename='delete_inboxmessages', content_type=inbox_ct),
        ]

        # Assign permissions to groups
        member_group.permissions.set(member_permissions)
        librarian_group.permissions.set(librarian_permissions)
        admin_group.permissions.set(admin_permissions)

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully created groups and assigned permissions:\n'
                f'- Member: {len(member_permissions)} permissions\n'
                f'- Librarian: {len(librarian_permissions)} permissions\n'
                f'- Library Admin: {len(admin_permissions)} permissions'
            )
        )

        # Display group information
        self.stdout.write('\nGroup Details:')
        for group in [member_group, librarian_group, admin_group]:
            self.stdout.write(f'\n{group.name}:')
            for perm in group.permissions.all():
                self.stdout.write(f'  - {perm.name}')