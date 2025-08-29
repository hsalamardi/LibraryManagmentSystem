from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Count, Q, Sum
from django.db import models
from datetime import date, timedelta
import json

from .decorators import librarian_required, LibrarianRequiredMixin
from .reports import LibraryReports
from .models import Book, Borrower, BookReservation
from library_users.models import UserProfileinfo


@method_decorator(librarian_required, name='dispatch')
class DashboardView(TemplateView):
    """Main dashboard view for librarians and admins"""
    template_name = 'books/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all dashboard data
        dashboard_data = LibraryReports.get_dashboard_summary()
        context.update(dashboard_data)
        
        # Add chart data
        context['chart_data'] = self.get_chart_data()
        
        return context
    
    def get_chart_data(self):
        """Prepare data for charts"""
        # Books by language chart
        books_by_language = Book.objects.values('language').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Monthly borrowings for the last 6 months
        monthly_data = []
        for i in range(6):
            target_date = date.today().replace(day=1) - timedelta(days=i*30)
            month_stats = LibraryReports.get_monthly_statistics(
                target_date.year, target_date.month
            )
            monthly_data.append({
                'month': target_date.strftime('%b %Y'),
                'borrowings': month_stats['monthly_borrowings'],
                'returns': month_stats['monthly_returns']
            })
        
        # User type distribution
        user_types = UserProfileinfo.objects.values('user_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'books_by_language': list(books_by_language),
            'monthly_borrowings': list(reversed(monthly_data)),
            'user_types': list(user_types),
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
    
    context = {
        'user_profile': user_profile,
        'current_borrowings': current_borrowings,
        'reservations': reservations,
        'borrowing_history': borrowing_history,
        'overdue_books': overdue_books,
        'books_due_soon': books_due_soon,
    }
    
    return render(request, 'books/user_dashboard.html', context)