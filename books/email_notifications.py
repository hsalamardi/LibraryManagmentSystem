from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from datetime import date, timedelta
from .models import Book, Borrower, BookReservation
from library_users.models import UserProfileinfo, InboxMessages
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications to library users"""
    
    @staticmethod
    def send_due_date_reminder(borrowing):
        """Send reminder email for books due soon"""
        try:
            user = borrowing.borrower.user
            if not borrowing.borrower.email_notifications:
                return False
            
            context = {
                'user': user,
                'borrowing': borrowing,
                'book': borrowing.book,
                'days_until_due': (borrowing.due_date - date.today()).days,
                'library_name': getattr(settings, 'LIBRARY_NAME', 'Library'),
                'library_email': getattr(settings, 'LIBRARY_EMAIL', 'library@example.com'),
            }
            
            # Render email templates
            html_message = render_to_string('emails/due_date_reminder.html', context)
            plain_message = strip_tags(html_message)
            
            subject = f"📚 Book Due Soon: {borrowing.book.title}"
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            # Create inbox message
            InboxMessages.objects.create(
                recipient=borrowing.borrower,
                message_type='reminder',
                subject=subject,
                message=f"Your book '{borrowing.book.title}' is due on {borrowing.due_date}. Please return it on time to avoid fines."
            )
            
            logger.info(f"Due date reminder sent to {user.email} for book {borrowing.book.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send due date reminder: {str(e)}")
            return False
    
    @staticmethod
    def send_overdue_notification(borrowing):
        """Send notification for overdue books"""
        try:
            user = borrowing.borrower.user
            if not borrowing.borrower.email_notifications:
                return False
            
            days_overdue = (date.today() - borrowing.due_date).days
            fine_amount = borrowing.calculate_fine()
            
            context = {
                'user': user,
                'borrowing': borrowing,
                'book': borrowing.book,
                'days_overdue': days_overdue,
                'fine_amount': fine_amount,
                'library_name': getattr(settings, 'LIBRARY_NAME', 'Library'),
                'library_email': getattr(settings, 'LIBRARY_EMAIL', 'library@example.com'),
                'library_phone': getattr(settings, 'LIBRARY_PHONE', 'N/A'),
            }
            
            # Render email templates
            html_message = render_to_string('emails/overdue_notification.html', context)
            plain_message = strip_tags(html_message)
            
            subject = f"⚠️ Overdue Book: {borrowing.book.title} - Fine: ${fine_amount:.2f}"
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            # Create inbox message
            InboxMessages.objects.create(
                recipient=borrowing.borrower,
                message_type='alert',
                subject=subject,
                message=f"Your book '{borrowing.book.title}' is {days_overdue} days overdue. Fine: ${fine_amount:.2f}. Please return immediately."
            )
            
            logger.info(f"Overdue notification sent to {user.email} for book {borrowing.book.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send overdue notification: {str(e)}")
            return False
    
    @staticmethod
    def send_reservation_available(reservation):
        """Send notification when reserved book becomes available"""
        try:
            user = reservation.user.user
            if not reservation.user.email_notifications:
                return False
            
            context = {
                'user': user,
                'reservation': reservation,
                'book': reservation.book,
                'expiry_date': reservation.expiry_date,
                'library_name': getattr(settings, 'LIBRARY_NAME', 'Library'),
                'library_email': getattr(settings, 'LIBRARY_EMAIL', 'library@example.com'),
            }
            
            # Render email templates
            html_message = render_to_string('emails/reservation_available.html', context)
            plain_message = strip_tags(html_message)
            
            subject = f"📖 Reserved Book Available: {reservation.book.title}"
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            # Create inbox message
            InboxMessages.objects.create(
                recipient=reservation.user,
                message_type='notification',
                subject=subject,
                message=f"Your reserved book '{reservation.book.title}' is now available for pickup. Please collect it before {reservation.expiry_date}."
            )
            
            logger.info(f"Reservation available notification sent to {user.email} for book {reservation.book.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reservation notification: {str(e)}")
            return False
    
    @staticmethod
    def send_reservation_expiry_warning(reservation):
        """Send warning when reservation is about to expire"""
        try:
            user = reservation.user.user
            if not reservation.user.email_notifications:
                return False
            
            days_until_expiry = (reservation.expiry_date.date() - date.today()).days
            
            context = {
                'user': user,
                'reservation': reservation,
                'book': reservation.book,
                'days_until_expiry': days_until_expiry,
                'expiry_date': reservation.expiry_date,
                'library_name': getattr(settings, 'LIBRARY_NAME', 'Library'),
                'library_email': getattr(settings, 'LIBRARY_EMAIL', 'library@example.com'),
            }
            
            # Render email templates
            html_message = render_to_string('emails/reservation_expiry_warning.html', context)
            plain_message = strip_tags(html_message)
            
            subject = f"⏰ Reservation Expiring Soon: {reservation.book.title}"
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            # Create inbox message
            InboxMessages.objects.create(
                recipient=reservation.user,
                message_type='reminder',
                subject=subject,
                message=f"Your reservation for '{reservation.book.title}' expires in {days_until_expiry} days. Please collect the book soon."
            )
            
            logger.info(f"Reservation expiry warning sent to {user.email} for book {reservation.book.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reservation expiry warning: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user_profile):
        """Send welcome email to new library members"""
        try:
            user = user_profile.user
            
            context = {
                'user': user,
                'user_profile': user_profile,
                'library_name': getattr(settings, 'LIBRARY_NAME', 'Library'),
                'library_email': getattr(settings, 'LIBRARY_EMAIL', 'library@example.com'),
                'library_address': getattr(settings, 'LIBRARY_ADDRESS', 'Library Address'),
                'library_phone': getattr(settings, 'LIBRARY_PHONE', 'N/A'),
            }
            
            # Render email templates
            html_message = render_to_string('emails/welcome_email.html', context)
            plain_message = strip_tags(html_message)
            
            subject = f"🎉 Welcome to {context['library_name']}!"
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            # Create inbox message
            InboxMessages.objects.create(
                recipient=user_profile,
                message_type='notification',
                subject=subject,
                message=f"Welcome to our library! Your account has been created successfully. You can now browse and borrow books."
            )
            
            logger.info(f"Welcome email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return False
    
    @staticmethod
    def send_book_return_confirmation(borrowing):
        """Send confirmation email when book is returned"""
        try:
            user = borrowing.borrower.user
            if not borrowing.borrower.email_notifications:
                return False
            
            context = {
                'user': user,
                'borrowing': borrowing,
                'book': borrowing.book,
                'return_date': borrowing.return_date,
                'fine_amount': borrowing.fine_amount,
                'library_name': getattr(settings, 'LIBRARY_NAME', 'Library'),
            }
            
            # Render email templates
            html_message = render_to_string('emails/return_confirmation.html', context)
            plain_message = strip_tags(html_message)
            
            subject = f"✅ Book Returned: {borrowing.book.title}"
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            logger.info(f"Return confirmation sent to {user.email} for book {borrowing.book.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send return confirmation: {str(e)}")
            return False


class NotificationScheduler:
    """Scheduler for automated email notifications"""
    
    @staticmethod
    def send_daily_reminders():
        """Send daily reminders for books due soon (3 days before)"""
        reminder_date = date.today() + timedelta(days=3)
        
        borrowings_due_soon = Borrower.objects.filter(
            due_date=reminder_date,
            status='borrowed'
        ).select_related('borrower__user', 'book')
        
        sent_count = 0
        for borrowing in borrowings_due_soon:
            if EmailNotificationService.send_due_date_reminder(borrowing):
                sent_count += 1
        
        logger.info(f"Sent {sent_count} due date reminders")
        return sent_count
    
    @staticmethod
    def send_overdue_notifications():
        """Send notifications for overdue books"""
        overdue_borrowings = Borrower.objects.filter(
            due_date__lt=date.today(),
            status='borrowed'
        ).select_related('borrower__user', 'book')
        
        sent_count = 0
        for borrowing in overdue_borrowings:
            if EmailNotificationService.send_overdue_notification(borrowing):
                sent_count += 1
        
        logger.info(f"Sent {sent_count} overdue notifications")
        return sent_count
    
    @staticmethod
    def send_reservation_expiry_warnings():
        """Send warnings for reservations expiring soon"""
        warning_date = date.today() + timedelta(days=1)  # 1 day before expiry
        
        expiring_reservations = BookReservation.objects.filter(
            expiry_date__date=warning_date,
            status='active'
        ).select_related('user__user', 'book')
        
        sent_count = 0
        for reservation in expiring_reservations:
            if EmailNotificationService.send_reservation_expiry_warning(reservation):
                sent_count += 1
        
        logger.info(f"Sent {sent_count} reservation expiry warnings")
        return sent_count
    
    @staticmethod
    def run_daily_notifications():
        """Run all daily notification tasks"""
        logger.info("Starting daily notification tasks")
        
        reminders = NotificationScheduler.send_daily_reminders()
        overdue = NotificationScheduler.send_overdue_notifications()
        expiry_warnings = NotificationScheduler.send_reservation_expiry_warnings()
        
        total_sent = reminders + overdue + expiry_warnings
        logger.info(f"Daily notifications completed. Total emails sent: {total_sent}")
        
        return {
            'reminders': reminders,
            'overdue': overdue,
            'expiry_warnings': expiry_warnings,
            'total': total_sent
        }