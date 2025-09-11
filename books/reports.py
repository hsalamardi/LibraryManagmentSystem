from django.db.models import Count, Q, Avg, Sum, F
from django.utils import timezone
from datetime import date, timedelta
from .models import Book, Borrower, BookReservation, BorrowRequest, ReturnRequest
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
    def get_request_statistics():
        """Get borrow and return request statistics"""
        # Borrow request stats
        total_borrow_requests = BorrowRequest.objects.count()
        pending_borrow_requests = BorrowRequest.objects.filter(status='pending').count()
        approved_borrow_requests = BorrowRequest.objects.filter(status='approved').count()
        denied_borrow_requests = BorrowRequest.objects.filter(status='denied').count()
        
        # Return request stats
        total_return_requests = ReturnRequest.objects.count()
        pending_return_requests = ReturnRequest.objects.filter(status='pending').count()
        approved_return_requests = ReturnRequest.objects.filter(status='approved').count()
        denied_return_requests = ReturnRequest.objects.filter(status='denied').count()
        
        # Recent requests (last 7 days)
        week_ago = date.today() - timedelta(days=7)
        recent_borrow_requests = BorrowRequest.objects.filter(request_date__gte=week_ago).count()
        recent_return_requests = ReturnRequest.objects.filter(request_date__gte=week_ago).count()
        
        return {
            'total_borrow_requests': total_borrow_requests,
            'pending_borrow_requests': pending_borrow_requests,
            'approved_borrow_requests': approved_borrow_requests,
            'denied_borrow_requests': denied_borrow_requests,
            'total_return_requests': total_return_requests,
            'pending_return_requests': pending_return_requests,
            'approved_return_requests': approved_return_requests,
            'denied_return_requests': denied_return_requests,
            'recent_borrow_requests': recent_borrow_requests,
            'recent_return_requests': recent_return_requests,
            'total_pending_requests': pending_borrow_requests + pending_return_requests,
        }
    
    @staticmethod
    def get_financial_statistics():
        """Get financial statistics"""
        # Total fines collected
        total_fines_collected = Borrower.objects.aggregate(
            total=Sum('fine_amount')
        )['total'] or 0
        
        # Outstanding fines
        outstanding_fines = UserProfileinfo.objects.aggregate(
            total=Sum('total_fines')
        )['total'] or 0
        
        # Average fine per overdue book
        overdue_with_fines = Borrower.objects.filter(
            status='borrowed',
            due_date__lt=date.today(),
            fine_amount__gt=0
        )
        avg_fine = overdue_with_fines.aggregate(avg=Avg('fine_amount'))['avg'] or 0
        
        # Monthly fine collection
        this_month_start = date.today().replace(day=1)
        monthly_fines = Borrower.objects.filter(
            return_date__gte=this_month_start,
            fine_amount__gt=0
        ).aggregate(total=Sum('fine_amount'))['total'] or 0
        
        return {
            'total_fines_collected': round(total_fines_collected, 2),
            'outstanding_fines': round(outstanding_fines, 2),
            'avg_fine_per_book': round(avg_fine, 2),
            'monthly_fines': round(monthly_fines, 2),
            'users_with_fines': UserProfileinfo.objects.filter(total_fines__gt=0).count(),
        }
    
    @staticmethod
    def get_system_health_statistics():
        """Get system health and performance statistics"""
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Activity metrics
        daily_activity = {
            'new_users_today': UserProfileinfo.objects.filter(membership_date=today).count(),
            'books_borrowed_today': Borrower.objects.filter(borrow_date=today).count(),
            'books_returned_today': Borrower.objects.filter(return_date=today).count(),
            'requests_submitted_today': (
                BorrowRequest.objects.filter(request_date__date=today).count() +
                ReturnRequest.objects.filter(request_date__date=today).count()
            ),
        }
        
        # Weekly trends
        weekly_activity = {
            'new_users_week': UserProfileinfo.objects.filter(membership_date__gte=week_ago).count(),
            'books_borrowed_week': Borrower.objects.filter(borrow_date__gte=week_ago).count(),
            'books_returned_week': Borrower.objects.filter(return_date__gte=week_ago).count(),
        }
        
        # Collection utilization
        total_books = Book.objects.count()
        books_never_borrowed = Book.objects.annotate(
            borrow_count=Count('borrowings')
        ).filter(borrow_count=0).count()
        
        utilization_rate = 0
        if total_books > 0:
            utilization_rate = ((total_books - books_never_borrowed) / total_books) * 100
        
        return {
            'daily_activity': daily_activity,
            'weekly_activity': weekly_activity,
            'collection_utilization_rate': round(utilization_rate, 1),
            'books_never_borrowed': books_never_borrowed,
            'avg_books_per_user': round(
                Borrower.objects.filter(status='borrowed').count() / 
                max(UserProfileinfo.objects.filter(status='active').count(), 1), 2
            ),
        }
    
    @staticmethod
    def get_top_performers():
        """Get top performing books, users, and other metrics"""
        # Most active borrowers
        top_borrowers = UserProfileinfo.objects.annotate(
            total_borrowed=Count('borrowed_books')
        ).filter(total_borrowed__gt=0).order_by('-total_borrowed')[:5]
        
        # Books with highest demand (reservations + borrows)
        high_demand_books = Book.objects.annotate(
            total_demand=Count('borrowings') + Count('reservations')
        ).filter(total_demand__gt=0).order_by('-total_demand')[:5]
        
        # Most efficient users (lowest overdue rate)
        efficient_users = UserProfileinfo.objects.annotate(
            total_borrows=Count('borrowed_books'),
            overdue_count=Count('borrowed_books', filter=Q(
                borrowed_books__due_date__lt=date.today(),
                borrowed_books__status='borrowed'
            ))
        ).filter(total_borrows__gte=3).order_by('overdue_count', '-total_borrows')[:5]
        
        return {
            'top_borrowers': top_borrowers,
            'high_demand_books': high_demand_books,
            'efficient_users': efficient_users,
        }
    
    @staticmethod
    def get_honor_board():
        """Get top 3 borrowers for honor dashboard"""
        from datetime import datetime, timedelta
        
        # Get top borrowers with detailed stats
        top_readers = UserProfileinfo.objects.annotate(
            total_borrowed=Count('borrowed_books'),
            books_returned=Count('borrowed_books', filter=Q(borrowed_books__status='returned')),
            current_borrowed=Count('borrowed_books', filter=Q(borrowed_books__status='borrowed')),
            overdue_count=Count('borrowed_books', filter=Q(
                borrowed_books__due_date__lt=date.today(),
                borrowed_books__status='borrowed'
            )),
            # Calculate reading score based on multiple factors
            reading_score=(
                Count('borrowed_books') * 10 +  # 10 points per book borrowed
                Count('borrowed_books', filter=Q(borrowed_books__status='returned')) * 5 +  # 5 bonus points for returning
                Count('borrowed_books', filter=Q(
                    borrowed_books__status='returned',
                    borrowed_books__return_date__lte=F('borrowed_books__due_date')
                )) * 3  # 3 bonus points for on-time return
            )
        ).filter(
            total_borrowed__gt=0,
            status='active'
        ).order_by('-reading_score', '-total_borrowed')[:3]
        
        # Add rank and achievement info
        honor_list = []
        achievements = [
            {'title': '🥇 Reading Champion', 'description': 'Most dedicated reader', 'color': '#FFD700'},
            {'title': '🥈 Book Explorer', 'description': 'Avid knowledge seeker', 'color': '#C0C0C0'},
            {'title': '🥉 Literary Enthusiast', 'description': 'Passionate reader', 'color': '#CD7F32'}
        ]
        
        for i, reader in enumerate(top_readers):
            # Calculate reading streak (consecutive months with borrowings)
            current_month = date.today().replace(day=1)
            streak = 0
            check_month = current_month
            
            for month_back in range(12):  # Check last 12 months
                if month_back == 0:
                    month_start = current_month
                else:
                    if check_month.month == 1:
                        check_month = check_month.replace(year=check_month.year-1, month=12)
                    else:
                        check_month = check_month.replace(month=check_month.month-1)
                    month_start = check_month
                
                if check_month.month == 12:
                    month_end = check_month.replace(year=check_month.year+1, month=1)
                else:
                    month_end = check_month.replace(month=check_month.month+1)
                
                monthly_borrows = reader.borrowed_books.filter(
                    borrow_date__gte=month_start,
                    borrow_date__lt=month_end
                ).count()
                
                if monthly_borrows > 0:
                    streak += 1
                else:
                    break
            
            # Calculate completion rate
            completion_rate = 0
            if reader.total_borrowed > 0:
                completion_rate = (reader.books_returned / reader.total_borrowed) * 100
            
            honor_data = {
                'rank': i + 1,
                'user': reader,
                'total_borrowed': reader.total_borrowed,
                'books_returned': reader.books_returned,
                'current_borrowed': reader.current_borrowed,
                'overdue_count': reader.overdue_count,
                'reading_score': reader.reading_score,
                'completion_rate': round(completion_rate, 1),
                'reading_streak': streak,
                'achievement': achievements[i] if i < len(achievements) else achievements[-1],
                'is_perfect_reader': reader.overdue_count == 0 and reader.total_borrowed >= 5,
                'monthly_average': round(reader.total_borrowed / max(streak, 1), 1)
            }
            honor_list.append(honor_data)
        
        return honor_list
    
    @staticmethod
    def get_dashboard_summary():
        """Get comprehensive summary data for dashboard"""
        return {
            'user_stats': LibraryReports.get_user_statistics(),
            'book_stats': LibraryReports.get_book_statistics(),
            'borrowing_stats': LibraryReports.get_borrowing_statistics(),
            'reservation_stats': LibraryReports.get_reservation_statistics(),
            'request_stats': LibraryReports.get_request_statistics(),
            'financial_stats': LibraryReports.get_financial_statistics(),
            'system_health': LibraryReports.get_system_health_statistics(),
            'top_performers': LibraryReports.get_top_performers(),
            'popular_books': LibraryReports.get_popular_books(5),
            'overdue_books': LibraryReports.get_overdue_books()[:10],
            'books_due_soon': LibraryReports.get_books_due_soon()[:10],
            'monthly_stats': LibraryReports.get_monthly_statistics(),
        }