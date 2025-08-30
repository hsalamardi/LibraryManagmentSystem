from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Count, Q, Sum
from django.db import models
from datetime import date, timedelta
import json

from .decorators import librarian_required, LibrarianRequiredMixin, is_librarian, is_admin
from .reports import LibraryReports
from .models import Book, Borrower, BookReservation
from library_users.models import UserProfileinfo
from django.shortcuts import redirect


class DashboardView(TemplateView):
    """Public library dashboard with valuable information for everyone - no login required"""
    template_name = 'books/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Public Library Statistics
        total_books = Book.objects.count()
        available_books = Book.objects.filter(is_available=True).count()
        borrowed_books = total_books - available_books
        
        # Collection Statistics
        total_users = UserProfileinfo.objects.count()
        active_borrowers = Borrower.objects.filter(
            return_date__isnull=True
        ).values('borrower').distinct().count()
        
        # Calculate collection utilization rate
        utilization_rate = round((borrowed_books / total_books * 100), 1) if total_books > 0 else 0
        
        # Get popular books (most borrowed)
        popular_books = Book.objects.annotate(
            borrow_count=Count('borrowings')
        ).filter(borrow_count__gt=0).order_by('-borrow_count')[:10]
        
        # Get recently added books
        recent_books = Book.objects.order_by('-date_added')[:8]
        
        # Get books by language distribution
        language_stats = Book.objects.values('language').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Get books by category/genre
        category_stats = Book.objects.values('main_class').annotate(
            count=Count('id')
        ).order_by('-count')[:8]
        
        # Library services and information
        library_info = {
            'name': 'NTA Digital Library',
            'description': 'Your gateway to knowledge and learning',
            'established': '2024',
            'mission': 'To provide free access to knowledge and foster a love of reading in our community',
            'services': [
                'Book Borrowing & Returns',
                'Digital Resources Access',
                'Research Assistance',
                'Reading Programs',
                'Study Spaces',
                'Community Events'
            ],
            'opening_hours': {
                'monday_friday': '8:00 AM - 8:00 PM',
                'saturday': '9:00 AM - 6:00 PM',
                'sunday': '12:00 PM - 5:00 PM'
            },
            'contact': {
                'phone': '+1 (555) 123-4567',
                'email': 'info@ntalibrary.com',
                'address': '123 Knowledge Street, Learning City, LC 12345'
            }
        }
        
        # Reading statistics for public interest
        from datetime import datetime
        today = date.today()
        reading_stats = {
            'books_borrowed_today': Borrower.objects.filter(
                borrow_date__year=today.year,
                borrow_date__month=today.month,
                borrow_date__day=today.day
            ).count(),
            'books_returned_today': Borrower.objects.filter(
                return_date__year=today.year,
                return_date__month=today.month,
                return_date__day=today.day
            ).count(),
            'most_active_day': 'Monday',  # Could be calculated from data
            'average_books_per_user': round(total_books / total_users, 1) if total_users > 0 else 0
        }
        
        context.update({
            # Basic Statistics
            'total_books': total_books,
            'available_books': available_books,
            'borrowed_books': borrowed_books,
            'total_users': total_users,
            'active_borrowers': active_borrowers,
            'utilization_rate': utilization_rate,
            
            # Public Information
            'library_info': library_info,
            'reading_stats': reading_stats,
            'popular_books': popular_books,
            'recent_books': recent_books,
            'language_stats': language_stats,
            'category_stats': category_stats,
            
            # Charts and Analytics
            'chart_data': self.get_chart_data(),
            
            # Public access flag
            'is_public_dashboard': True,
        })
        
        return context
    
    def get_chart_data(self):
        """Prepare comprehensive data for charts and analytics"""
        # Books by language chart
        books_by_language = Book.objects.values('language').annotate(
            count=Count('id')
        ).order_by('-count')[:8]
        
        # Monthly borrowings for the last 12 months
        monthly_data = []
        for i in range(12):
            target_date = date.today().replace(day=1) - timedelta(days=i*30)
            month_stats = LibraryReports.get_monthly_statistics(
                target_date.year, target_date.month
            )
            monthly_data.append({
                'month': target_date.strftime('%b %Y'),
                'borrowings': month_stats['monthly_borrowings'],
                'returns': month_stats['monthly_returns'],
                'new_users': month_stats['new_users'],
                'new_books': month_stats['new_books']
            })
        
        # User type distribution
        user_types = UserProfileinfo.objects.values('user_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Books by genre/category (using main_class as category)
        books_by_category = Book.objects.values('main_class').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Reading trends - books borrowed by month
        reading_trends = []
        for i in range(6):
            target_date = date.today().replace(day=1) - timedelta(days=i*30)
            borrowings_count = Borrower.objects.filter(
                borrow_date__year=target_date.year,
                borrow_date__month=target_date.month
            ).count()
            reading_trends.append({
                'month': target_date.strftime('%b'),
                'count': borrowings_count
            })
        
        # Popular authors (top 10)
        popular_authors = Book.objects.values('author').annotate(
            borrow_count=Count('borrowings')
        ).filter(borrow_count__gt=0).order_by('-borrow_count')[:10]
        
        # Book condition distribution
        book_conditions = Book.objects.values('condition').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Weekly activity (last 4 weeks)
        weekly_activity = []
        for i in range(4):
            week_start = date.today() - timedelta(days=(i+1)*7)
            week_end = week_start + timedelta(days=6)
            
            weekly_borrowings = Borrower.objects.filter(
                borrow_date__range=[week_start, week_end]
            ).count()
            
            weekly_returns = Borrower.objects.filter(
                return_date__range=[week_start, week_end]
            ).count()
            
            weekly_activity.append({
                'week': f'Week {4-i}',
                'borrowings': weekly_borrowings,
                'returns': weekly_returns
            })
        
        # User engagement metrics
        total_users = UserProfileinfo.objects.filter(status='active').count()
        users_with_books = UserProfileinfo.objects.filter(current_books_count__gt=0).count()
        engagement_rate = (users_with_books / max(total_users, 1)) * 100
        
        # Reading completion rate
        total_borrowings = Borrower.objects.count()
        completed_borrowings = Borrower.objects.filter(status='returned').count()
        completion_rate = (completed_borrowings / max(total_borrowings, 1)) * 100
        
        return {
            'books_by_language': list(books_by_language),
            'monthly_borrowings': list(reversed(monthly_data)),
            'user_types': list(user_types),
            'books_by_category': list(books_by_category),
            'reading_trends': list(reversed(reading_trends)),
            'popular_authors': list(popular_authors),
            'book_conditions': list(book_conditions),
            'weekly_activity': list(reversed(weekly_activity)),
            'engagement_rate': round(engagement_rate, 1),
            'completion_rate': round(completion_rate, 1),
            'total_books_borrowed': total_borrowings,
            'active_readers': users_with_books
        }


@librarian_required
def reports_view(request):
    """Detailed reports view"""
    context = {
        'popular_books': LibraryReports.get_popular_books(20),
        'overdue_books': LibraryReports.get_overdue_books(),
        'books_due_soon': LibraryReports.get_books_due_soon(),
        'user_stats': LibraryReports.get_user_statistics(),
        'book_stats': LibraryReports.get_book_statistics(),
        'borrowing_stats': LibraryReports.get_borrowing_statistics(),
        'reservation_stats': LibraryReports.get_reservation_statistics(),
    }
    return render(request, 'books/reports.html', context)


@librarian_required
def analytics_api(request):
    """API endpoint for analytics data"""
    report_type = request.GET.get('type', 'summary')
    
    if report_type == 'summary':
        data = LibraryReports.get_dashboard_summary()
    elif report_type == 'popular_books':
        books = LibraryReports.get_popular_books(10)
        data = [{
            'title': book.title,
            'author': book.author,
            'borrow_count': book.borrow_count
        } for book in books]
    elif report_type == 'overdue':
        overdue = LibraryReports.get_overdue_books()
        data = [{
            'book_title': borrowing.book.title,
            'borrower': borrowing.borrower.user.get_full_name(),
            'due_date': borrowing.due_date.isoformat(),
            'days_overdue': (date.today() - borrowing.due_date).days
        } for borrowing in overdue]
    elif report_type == 'monthly':
        year = int(request.GET.get('year', date.today().year))
        month = int(request.GET.get('month', date.today().month))
        data = LibraryReports.get_monthly_statistics(year, month)
    else:
        data = {'error': 'Invalid report type'}
    
    return JsonResponse(data, safe=False)


@librarian_required
def user_activity_report(request):
    """User activity report"""
    # Most active users (by borrowing count)
    active_users = UserProfileinfo.objects.annotate(
        total_borrowings=Count('borrowed_books')
    ).filter(
        total_borrowings__gt=0
    ).order_by('-total_borrowings')[:20]
    
    # Users with overdue books
    users_with_overdue = UserProfileinfo.objects.filter(
        borrowed_books__due_date__lt=date.today(),
        borrowed_books__status='borrowed'
    ).distinct()
    
    # Users with highest fines
    users_with_fines = UserProfileinfo.objects.filter(
        total_fines__gt=0
    ).order_by('-total_fines')[:10]
    
    context = {
        'active_users': active_users,
        'users_with_overdue': users_with_overdue,
        'users_with_fines': users_with_fines,
    }
    
    return render(request, 'books/user_activity_report.html', context)


@librarian_required
def book_usage_report(request):
    """Book usage and popularity report"""
    # Most popular books
    popular_books = LibraryReports.get_popular_books(50)
    
    # Least popular books (never borrowed)
    unpopular_books = Book.objects.annotate(
        borrow_count=Count('borrowings')
    ).filter(borrow_count=0)[:20]
    
    # Books by category/subject
    books_by_category = Book.objects.values('main_class').annotate(
        count=Count('id')
    ).filter(
        main_class__isnull=False
    ).order_by('-count')[:10]
    
    # Recently added books
    recent_books = Book.objects.filter(
        date_added__gte=date.today() - timedelta(days=30)
    ).order_by('-date_added')[:20]
    
    context = {
        'popular_books': popular_books,
        'unpopular_books': unpopular_books,
        'books_by_category': books_by_category,
        'recent_books': recent_books,
    }
    
    return render(request, 'books/book_usage_report.html', context)


@librarian_required
def financial_report(request):
    """Financial report showing fines and revenue"""
    # Total fines collected
    total_fines = Borrower.objects.aggregate(
        total=models.Sum('fine_amount')
    )['total'] or 0
    
    # Fines by month for the last 12 months
    monthly_fines = []
    for i in range(12):
        target_date = date.today().replace(day=1) - timedelta(days=i*30)
        month_fines = Borrower.objects.filter(
            return_date__year=target_date.year,
            return_date__month=target_date.month,
            fine_amount__gt=0
        ).aggregate(
            total=models.Sum('fine_amount')
        )['total'] or 0
        
        monthly_fines.append({
            'month': target_date.strftime('%b %Y'),
            'fines': float(month_fines)
        })
    
    # Users with outstanding fines
    users_with_fines = UserProfileinfo.objects.filter(
        total_fines__gt=0
    ).order_by('-total_fines')
    
    context = {
        'total_fines': total_fines,
        'monthly_fines': list(reversed(monthly_fines)),
        'users_with_fines': users_with_fines,
    }
    
    return render(request, 'books/financial_report.html', context)


@login_required
def user_dashboard(request):
    """Dashboard for regular users"""
    if not hasattr(request.user, 'userprofileinfo'):
        return render(request, 'books/user_dashboard.html', {'no_profile': True})
    
    user_profile = request.user.userprofileinfo
    
    # User's current borrowings
    current_borrowings = Borrower.objects.filter(
        borrower=user_profile,
        status='borrowed'
    ).select_related('book')
    
    # User's reservations
    reservations = BookReservation.objects.filter(
        user=user_profile,
        status='active'
    ).select_related('book')
    
    # User's borrowing history
    borrowing_history = Borrower.objects.filter(
        borrower=user_profile
    ).select_related('book').order_by('-borrow_date')[:10]
    
    # Overdue books
    overdue_books = current_borrowings.filter(
        due_date__lt=date.today()
    )
    
    # Books due soon
    books_due_soon = current_borrowings.filter(
        due_date__lte=date.today() + timedelta(days=3),
        due_date__gte=date.today()
    )
    
    # Calculate available books (max allowed minus currently borrowed)
    available_books = user_profile.max_books_allowed - user_profile.current_books_count
    
    # Calculate borrowing capacity percentage
    if user_profile.max_books_allowed > 0:
        borrowing_percentage = (user_profile.current_books_count / user_profile.max_books_allowed) * 100
    else:
        borrowing_percentage = 0
    
    # Calculate dates for template comparisons
    today = date.today()
    due_soon_date = today + timedelta(days=3)
    
    context = {
        'user_profile': user_profile,
        'current_borrowings': current_borrowings,
        'reservations': reservations,
        'borrowing_history': borrowing_history,
        'overdue_books': overdue_books,
        'books_due_soon': books_due_soon,
        'available_books': available_books,
        'borrowing_percentage': borrowing_percentage,
        'today': today,
        'due_soon_date': due_soon_date,
    }
    
    return render(request, 'books/user_dashboard.html', context)


@login_required
def dashboard_redirect(request):
    """Redirect users to appropriate dashboard based on their role"""
    # Check if user is librarian or admin
    if is_librarian(request.user) or is_admin(request.user):
        # Redirect to admin dashboard
        return redirect('books:admin_dashboard')
    else:
        # Redirect to user dashboard
        return redirect('books:user_dashboard')