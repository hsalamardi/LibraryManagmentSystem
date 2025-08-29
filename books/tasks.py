from celery import shared_task
from django.core.mail import mail_admins
from .email_notifications import NotificationScheduler, EmailNotificationService
from .models import Borrower, BookReservation
from library_users.models import UserProfileinfo
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_daily_notifications():
    """Celery task to send daily email notifications"""
    try:
        results = NotificationScheduler.run_daily_notifications()
        
        # Log results
        logger.info(
            f"Daily notifications completed: "
            f"reminders={results['reminders']}, "
            f"overdue={results['overdue']}, "
            f"expiry_warnings={results['expiry_warnings']}, "
            f"total={results['total']}"
        )
        
        # Send summary to admins if there were any notifications
        if results['total'] > 0:
            mail_admins(
                subject='Daily Library Notifications Summary',
                message=f"Daily notification task completed successfully.\n\n"
                       f"Due date reminders sent: {results['reminders']}\n"
                       f"Overdue notifications sent: {results['overdue']}\n"
                       f"Reservation expiry warnings sent: {results['expiry_warnings']}\n"
                       f"Total emails sent: {results['total']}"
            )
        
        return results
        
    except Exception as e:
        logger.error(f"Daily notifications task failed: {str(e)}")
        
        # Notify admins of failure
        mail_admins(
            subject='Library Notifications Task Failed',
            message=f"The daily notifications task failed with error: {str(e)}"
        )
        
        raise


@shared_task
def send_due_date_reminders():
    """Celery task to send due date reminders"""
    try:
        count = NotificationScheduler.send_daily_reminders()
        logger.info(f"Sent {count} due date reminder emails")
        return count
    except Exception as e:
        logger.error(f"Due date reminders task failed: {str(e)}")
        raise


@shared_task
def send_overdue_notifications():
    """Celery task to send overdue notifications"""
    try:
        count = NotificationScheduler.send_overdue_notifications()
        logger.info(f"Sent {count} overdue notification emails")
        return count
    except Exception as e:
        logger.error(f"Overdue notifications task failed: {str(e)}")
        raise


@shared_task
def send_reservation_expiry_warnings():
    """Celery task to send reservation expiry warnings"""
    try:
        count = NotificationScheduler.send_reservation_expiry_warnings()
        logger.info(f"Sent {count} reservation expiry warning emails")
        return count
    except Exception as e:
        logger.error(f"Reservation expiry warnings task failed: {str(e)}")
        raise


@shared_task
def send_welcome_email(user_profile_id):
    """Celery task to send welcome email to new users"""
    try:
        user_profile = UserProfileinfo.objects.get(id=user_profile_id)
        success = EmailNotificationService.send_welcome_email(user_profile)
        
        if success:
            logger.info(f"Welcome email sent to {user_profile.user.email}")
        else:
            logger.warning(f"Failed to send welcome email to {user_profile.user.email}")
        
        return success
        
    except UserProfileinfo.DoesNotExist:
        logger.error(f"User profile with ID {user_profile_id} not found")
        return False
    except Exception as e:
        logger.error(f"Welcome email task failed: {str(e)}")
        raise


@shared_task
def send_reservation_available_notification(reservation_id):
    """Celery task to send reservation available notification"""
    try:
        reservation = BookReservation.objects.get(id=reservation_id)
        success = EmailNotificationService.send_reservation_available(reservation)
        
        if success:
            logger.info(f"Reservation available notification sent for book {reservation.book.title}")
        else:
            logger.warning(f"Failed to send reservation notification for book {reservation.book.title}")
        
        return success
        
    except BookReservation.DoesNotExist:
        logger.error(f"Reservation with ID {reservation_id} not found")
        return False
    except Exception as e:
        logger.error(f"Reservation notification task failed: {str(e)}")
        raise


@shared_task
def send_return_confirmation(borrowing_id):
    """Celery task to send book return confirmation"""
    try:
        borrowing = Borrower.objects.get(id=borrowing_id)
        success = EmailNotificationService.send_book_return_confirmation(borrowing)
        
        if success:
            logger.info(f"Return confirmation sent for book {borrowing.book.title}")
        else:
            logger.warning(f"Failed to send return confirmation for book {borrowing.book.title}")
        
        return success
        
    except Borrower.DoesNotExist:
        logger.error(f"Borrowing with ID {borrowing_id} not found")
        return False
    except Exception as e:
        logger.error(f"Return confirmation task failed: {str(e)}")
        raise


@shared_task
def cleanup_expired_reservations():
    """Celery task to clean up expired reservations"""
    try:
        from datetime import date
        
        expired_reservations = BookReservation.objects.filter(
            expiry_date__date__lt=date.today(),
            status='active'
        )
        
        count = expired_reservations.count()
        
        # Update status to expired
        expired_reservations.update(status='expired')
        
        logger.info(f"Marked {count} reservations as expired")
        return count
        
    except Exception as e:
        logger.error(f"Cleanup expired reservations task failed: {str(e)}")
        raise


@shared_task
def generate_weekly_report():
    """Celery task to generate and send weekly library report"""
    try:
        from datetime import date, timedelta
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        from .reports import LibraryReports
        
        # Get weekly statistics
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        # Generate report data
        report_data = {
            'start_date': start_date,
            'end_date': end_date,
            'dashboard_summary': LibraryReports.get_dashboard_summary(),
            'popular_books': LibraryReports.get_popular_books(10),
            'overdue_count': len(LibraryReports.get_overdue_books()),
        }
        
        # Render email template
        html_content = render_to_string('emails/weekly_report.html', report_data)
        
        # Send to admins
        subject = f"Weekly Library Report - {start_date} to {end_date}"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Please see the attached weekly library report.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin[1] for admin in settings.ADMINS]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Weekly report sent for period {start_date} to {end_date}")
        return True
        
    except Exception as e:
        logger.error(f"Weekly report task failed: {str(e)}")
        raise