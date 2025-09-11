from django.core.management.base import BaseCommand
from django.conf import settings
from books.email_notifications import NotificationScheduler
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send automated email notifications for library system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['all', 'reminders', 'overdue', 'reservations'],
            default='all',
            help='Type of notifications to send'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails'
        )

    def handle(self, *args, **options):
        notification_type = options['type']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No emails will be sent')
            )
        
        self.stdout.write(f'Starting {notification_type} notifications...')
        
        try:
            if notification_type == 'all':
                results = NotificationScheduler.run_daily_notifications()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Daily notifications completed:\n'
                        f'  - Due date reminders: {results["reminders"]}\n'
                        f'  - Overdue notifications: {results["overdue"]}\n'
                        f'  - Reservation warnings: {results["expiry_warnings"]}\n'
                        f'  - Total emails sent: {results["total"]}'
                    )
                )
                
            elif notification_type == 'reminders':
                count = NotificationScheduler.send_daily_reminders()
                self.stdout.write(
                    self.style.SUCCESS(f'Sent {count} due date reminder emails')
                )
                
            elif notification_type == 'overdue':
                count = NotificationScheduler.send_overdue_notifications()
                self.stdout.write(
                    self.style.SUCCESS(f'Sent {count} overdue notification emails')
                )
                
            elif notification_type == 'reservations':
                count = NotificationScheduler.send_reservation_expiry_warnings()
                self.stdout.write(
                    self.style.SUCCESS(f'Sent {count} reservation expiry warning emails')
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending notifications: {str(e)}')
            )
            logger.error(f'Notification command failed: {str(e)}')
            raise
        
        self.stdout.write(
            self.style.SUCCESS('Notification task completed successfully')
        )