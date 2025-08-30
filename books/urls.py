from django.urls import path
from . import views
from .views import BooksListView, BooksDetailView, SearchResultsView
from . import dashboard_views

app_name = 'books'
urlpatterns = [
    # Main pages
    path('', views.landing, name='landing'),
    path('books/', views.books, name='view_books'),
    path('books/list/', BooksListView.as_view(), name='view_books_list'),
    path('books/search/', SearchResultsView.as_view(), name='search_results'),
    path('books/add/', views.form_name_view, name='add_a_book'),
    path('books/<int:pk>/', BooksDetailView.as_view(), name='book_detail'),
    
    # Borrowing and returning
    path('books/<int:book_id>/borrow/', views.borrow_book, name='borrow_book'),
    path('borrowing/<int:borrowing_id>/return/', views.return_book, name='return_book'),
    
    # Borrow Requests Management
    path('borrow-requests/', views.manage_borrow_requests, name='manage_borrow_requests'),
    path('borrow-requests/<int:request_id>/approve/', views.approve_borrow_request, name='approve_borrow_request'),
    path('borrow-requests/<int:request_id>/deny/', views.deny_borrow_request, name='deny_borrow_request'),
    
    # Return Requests Management
    path('return-requests/', views.manage_borrow_requests, name='manage_return_requests'),  # Use the same view for return requests
    path('return-requests/<int:request_id>/approve/', views.approve_return_request, name='approve_return_request'),
    path('return-requests/<int:request_id>/deny/', views.deny_return_request, name='deny_return_request'),
    
    # Reservations
    path('books/<int:book_id>/reserve/', views.reserve_book, name='reserve_book'),
    
    # User's books
    path('my-books/', views.my_books, name='my_books'),
    
    # Barcode scanning
    path('barcode-scan/', views.barcode_scan, name='barcode_scan'),
    path('api/barcode-lookup/', views.barcode_lookup_api, name='barcode_lookup_api'),
    path('books/<int:book_id>/quick-borrow/', views.quick_borrow, name='quick_borrow'),
    
    # Dashboard and Reports
    path('dashboard/', dashboard_views.dashboard_redirect, name='dashboard'),
    path('admin-dashboard/', dashboard_views.DashboardView.as_view(), name='admin_dashboard'),
    path('user-dashboard/', dashboard_views.user_dashboard, name='user_dashboard'),
    path('reports/', dashboard_views.reports_view, name='reports'),
    path('reports/users/', dashboard_views.user_activity_report, name='user_activity_report'),
    path('reports/books/', dashboard_views.book_usage_report, name='book_usage_report'),
    path('reports/financial/', dashboard_views.financial_report, name='financial_report'),
    
    # API endpoints
    path('api/analytics/', dashboard_views.analytics_api, name='analytics_api'),
]