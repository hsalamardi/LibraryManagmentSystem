from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from datetime import date, timedelta
from .models import Book, Borrower, BookReservation
from library_users.models import UserProfileinfo


class LibraryReports:
    """Library analytics and reporting utilities"""
    
    @staticmethod
    def get_popular_books(limit=10):
        """Get most borrowed books"""
        return Book.objects.annotate(
            borrow_count=Count('borrowings')
        ).filter(
            borrow_count__gt=0
        ).order_by('-borrow_count')[:limit]
    
    @staticmethod
    def get_overdue_books():
        """Get all overdue books"""
        today = date.today()
        return Borrower.objects.filter(
            due_date__lt=today,
            status='borrowed'
        ).select_related('book', 'borrower__user')
    
    @staticmethod
    def get_books_due_soon(days=3):
        """Get books due within specified days"""
        due_date = date.today() + timedelta(days=days)
        return Borrower.objects.filter(
            due_date__lte=due_date,
            due_date__gte=date.today(),
            status='borrowed'
        ).select_related('book', 'borrower__user')
    
    @staticmethod
    def get_user_statistics():
        """Get user statistics"""
        total_users = UserProfileinfo.objects.count()
        active_users = UserProfileinfo.objects.filter(status='active').count()
        users_with_books = UserProfileinfo.objects.filter(
            current_books_count__gt=0
        ).count()
        users_with_fines = UserProfileinfo.objects.filter(
            total_fines__gt=0
        ).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'users_with_books': users_with_books,
            'users_with_fines': users_with_fines,
            'inactive_users': total_users - active_users,
        }
    
    @staticmethod
    def get_book_statistics():
        """Get book statistics"""
        total_books = Book.objects.count()
        available_books = Book.objects.filter(is_available=True).count()
        borrowed_books = Book.objects.filter(is_available=False).count()
        
        # Books by language
        books_by_language = Book.objects.values('language').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Books by condition
        books_by_condition = Book.objects.values('condition').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'total_books': total_books,
            'available_books': available_books,
            'borrowed_books': borrowed_books,
            'books_by_language': list(books_by_language),
            'books_by_condition': list(books_by_condition),
        }
    
    @staticmethod
    def get_borrowing_statistics():
        """Get borrowing statistics"""
        total_borrowings = Borrower.objects.count()
        active_borrowings = Borrower.objects.filter(status='borrowed').count()
        overdue_borrowings = Borrower.objects.filter(
            due_date__lt=date.today(),
            status='borrowed'
        ).count()
        returned_borrowings = Borrower.objects.filter(status='returned').count()
        
        # Average borrowing period
        returned_books = Borrower.objects.filter(
            status='returned',
            return_date__isnull=False
        )
        
        avg_borrowing_days = 0
        if returned_books.exists():
            total_days = sum([
                (b.return_date - b.borrow_date).days 
                for b in returned_books
            ])
            avg_borrowing_days = total_days / returned_books.count()
        
        # Total fines collected
        total_fines = Borrower.objects.aggregate(
            total=Sum('fine_amount')
        )['total'] or 0
        
        return {
            'total_borrowings': total_borrowings,
            'active_borrowings': active_borrowings,
            'overdue_borrowings': overdue_borrowings,
            'returned_borrowings': returned_borrowings,
            'avg_borrowing_days': round(avg_borrowing_days, 1),
            'total_fines': total_fines,
        }
    
    @staticmethod
    def get_reservation_statistics():
        """Get reservation statistics"""
        total_reservations = BookReservation.objects.count()
        active_reservations = BookReservation.objects.filter(status='active').count()
        fulfilled_reservations = BookReservation.objects.filter(status='fulfilled').count()
        expired_reservations = BookReservation.objects.filter(status='expired').count()
        
        # Most reserved books
        most_reserved = Book.objects.annotate(
            reservation_count=Count('reservations')
        ).filter(
            reservation_count__gt=0
        ).order_by('-reservation_count')[:5]
        
        return {
            'total_reservations': total_reservations,
            'active_reservations': active_reservations,
            'fulfilled_reservations': fulfilled_reservations,
            'expired_reservations': expired_reservations,
            'most_reserved_books': most_reserved,
        }
    
    @staticmethod
    def get_monthly_statistics(year=None, month=None):
        """Get statistics for a specific month"""
        if not year:
            year = date.today().year
        if not month:
            month = date.today().month
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        # Borrowings in the month
        monthly_borrowings = Borrower.objects.filter(
            borrow_date__gte=start_date,
            borrow_date__lt=end_date
        ).count()
        
        # Returns in the month
        monthly_returns = Borrower.objects.filter(
            return_date__gte=start_date,
            return_date__lt=end_date
        ).count()
        
        # New users in the month
        new_users = UserProfileinfo.objects.filter(
            membership_date__gte=start_date,
            membership_date__lt=end_date
        ).count()
        
        # Books added in the month
        new_books = Book.objects.filter(
            date_added__gte=start_date,
            date_added__lt=end_date
        ).count()
        
        return {
            'year': year,
            'month': month,
            'monthly_borrowings': monthly_borrowings,
            'monthly_returns': monthly_returns,
            'new_users': new_users,
            'new_books': new_books,
        }
    
    @staticmethod
    def get_dashboard_summary():
        """Get summary data for dashboard"""
        return {
            'user_stats': LibraryReports.get_user_statistics(),
            'book_stats': LibraryReports.get_book_statistics(),
            'borrowing_stats': LibraryReports.get_borrowing_statistics(),
            'reservation_stats': LibraryReports.get_reservation_statistics(),
            'popular_books': LibraryReports.get_popular_books(5),
            'overdue_books': LibraryReports.get_overdue_books()[:10],
            'books_due_soon': LibraryReports.get_books_due_soon()[:10],
            'monthly_stats': LibraryReports.get_monthly_statistics(),
        }