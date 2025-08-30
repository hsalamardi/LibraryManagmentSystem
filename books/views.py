from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count
from django.core.paginator import Paginator
from datetime import date, timedelta
from .models import Book, Borrower, BookReservation, BorrowRequest, ReturnRequest
from library_users.models import UserProfileinfo
from .forms import NewBook_form, NewBorrower_form, BarcodeScanForm
from .email_notifications import EmailNotificationService
from .tasks import send_welcome_email, send_return_confirmation, send_reservation_available_notification
from .decorators import librarian_required, is_librarian, is_admin
from django.utils import timezone
from .reports import LibraryReports


# Create your views here.

def landing(request):
    """Landing page with library statistics and honor board"""
    total_books = Book.objects.count()
    available_books = Book.objects.filter(is_available=True).count()
    borrowed_books = Borrower.objects.filter(status='borrowed').count()
    total_users = UserProfileinfo.objects.filter(status='active').count()
    
    # Get honor board data
    honor_board = LibraryReports.get_honor_board()
    
    context = {
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'total_users': total_users,
        'honor_board': honor_board,
    }
    return render(request, "landing_page.html", context=context)


@method_decorator(login_required(login_url='/library_users/register'), name='dispatch')
class BooksListView(ListView):
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 20
    ordering = ['title']
    
    def get_queryset(self):
        queryset = Book.objects.all()
        
        # Filter by availability
        availability = self.request.GET.get('availability')
        if availability == 'available':
            queryset = queryset.filter(is_available=True)
        elif availability == 'borrowed':
            queryset = queryset.filter(is_available=False)
        
        # Filter by language
        language = self.request.GET.get('language')
        if language:
            queryset = queryset.filter(language=language)
        
        # Advanced search functionality with ranking and multiple search modes
        search_query = self.request.GET.get('q')
        if search_query:
            from django.db.models import Case, When, IntegerField, Value, Count
            
            # Clean and prepare search query
            search_query = search_query.strip()
            search_terms = search_query.split()
            search_type = self.request.GET.get('search_type', 'smart')
            sort_by = self.request.GET.get('sort_by', 'relevance')
            
            # Build search filter based on search type
            if search_type == 'exact':
                # Exact phrase matching only
                combined_filter = (
                    Q(title__icontains=search_query) |
                    Q(author__icontains=search_query) |
                    Q(series__icontains=search_query) |
                    Q(publisher__icontains=search_query) |
                    Q(keywords__icontains=search_query) |
                    Q(isbn__icontains=search_query) |
                    Q(book_summary__icontains=search_query)
                )
            elif search_type == 'any':
                # Any word matching (OR logic)
                any_word_filter = Q()
                for term in search_terms:
                    term_filter = (
                        Q(title__icontains=term) |
                        Q(author__icontains=term) |
                        Q(series__icontains=term) |
                        Q(publisher__icontains=term) |
                        Q(keywords__icontains=term)
                    )
                    any_word_filter |= term_filter
                combined_filter = any_word_filter
            elif search_type == 'all':
                # All words required (AND logic)
                all_words_filter = Q()
                for term in search_terms:
                    term_filter = (
                        Q(title__icontains=term) |
                        Q(author__icontains=term) |
                        Q(series__icontains=term) |
                        Q(publisher__icontains=term) |
                        Q(keywords__icontains=term)
                    )
                    all_words_filter &= term_filter
                combined_filter = all_words_filter
            else:
                # Smart search (default) - combines multiple strategies
                exact_match = (
                    Q(title__iexact=search_query) |
                    Q(author__iexact=search_query)
                )
                
                high_priority = (
                    Q(title__icontains=search_query) |
                    Q(author__icontains=search_query)
                )
                
                medium_priority = (
                    Q(series__icontains=search_query) |
                    Q(publisher__icontains=search_query) |
                    Q(keywords__icontains=search_query)
                )
                
                low_priority = (
                    Q(isbn__icontains=search_query) |
                    Q(barcode__icontains=search_query) |
                    Q(editor__icontains=search_query) |
                    Q(translator__icontains=search_query) |
                    Q(book_summary__icontains=search_query)
                )
                
                multi_word_filter = Q()
                if len(search_terms) > 1:
                    for term in search_terms:
                        term_filter = (
                            Q(title__icontains=term) |
                            Q(author__icontains=term) |
                            Q(keywords__icontains=term) |
                            Q(series__icontains=term) |
                            Q(publisher__icontains=term)
                        )
                        multi_word_filter &= term_filter
                
                starts_with = (
                    Q(title__istartswith=search_query) |
                    Q(author__istartswith=search_query)
                )
                
                combined_filter = (
                    exact_match | high_priority | medium_priority | 
                    low_priority | multi_word_filter | starts_with
                )
            
            # Apply search filter
            queryset = queryset.filter(combined_filter)
            
            # Add relevance scoring and sorting
            if sort_by == 'relevance' or search_type == 'smart':
                queryset = queryset.annotate(
                    relevance_score=Case(
                        When(Q(title__iexact=search_query) | Q(author__iexact=search_query), then=Value(100)),
                        When(Q(title__istartswith=search_query) | Q(author__istartswith=search_query), then=Value(90)),
                        When(Q(title__icontains=search_query) | Q(author__icontains=search_query), then=Value(80)),
                        When(Q(series__icontains=search_query) | Q(publisher__icontains=search_query), then=Value(60)),
                        default=Value(40),
                        output_field=IntegerField()
                    )
                )
            
            # Apply sorting
            if sort_by == 'title':
                queryset = queryset.order_by('title')
            elif sort_by == 'author':
                queryset = queryset.order_by('author')
            elif sort_by == 'date_added':
                queryset = queryset.order_by('-date_added')
            elif sort_by == 'popularity':
                # Sort by number of borrowings (most borrowed first)
                queryset = queryset.annotate(
                    borrow_count=Count('borrowings')
                ).order_by('-borrow_count', 'title')
            else:
                # Default to relevance sorting
                queryset = queryset.order_by('-relevance_score', 'title')
            
            # Remove duplicates while preserving order
            queryset = queryset.distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['languages'] = Book.LANGUAGE_CHOICES
        context['current_filters'] = {
            'availability': self.request.GET.get('availability', ''),
            'language': self.request.GET.get('language', ''),
            'q': self.request.GET.get('q', ''),
        }
        return context


@method_decorator(login_required(login_url='/library_users/register'), name='dispatch')
class BooksDetailView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book_detail'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        
        # Check if user can borrow this book
        if hasattr(self.request.user, 'userprofileinfo'):
            user_profile = self.request.user.userprofileinfo
            context['can_borrow'] = (book.is_available and 
                                    user_profile.can_borrow_books)
            
            # Check if user has reserved this book
            context['has_reservation'] = BookReservation.objects.filter(
                book=book, 
                user=user_profile, 
                status='active'
            ).exists()
        else:
            context['can_borrow'] = False
            context['has_reservation'] = False
        
        # Get current borrower if book is borrowed
        if not book.is_available:
            current_borrowing = Borrower.objects.filter(
                book=book, 
                status='borrowed'
            ).first()
            context['current_borrowing'] = current_borrowing
        
        # Get pending borrow requests for this book
        pending_requests = BorrowRequest.objects.filter(
            book=book,
            status='pending'
        ).select_related('requester__user').order_by('-request_date')
        context['pending_requests'] = pending_requests
        
        # Check if current user has a pending request
        if hasattr(self.request.user, 'userprofileinfo'):
            user_has_pending_request = BorrowRequest.objects.filter(
                book=book,
                requester=self.request.user.userprofileinfo,
                status='pending'
            ).exists()
            context['user_has_pending_request'] = user_has_pending_request
        else:
            context['user_has_pending_request'] = False
        
        return context

def books(request):
    """Simple books view - redirects to BooksListView"""
    return redirect('books:view_books_list')


@librarian_required(redirect_url='/library_users/login/')
def form_name_view(request):
    """Add new book form - Only librarians and admins can add books"""
    if request.method == "POST":
        form = NewBook_form(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" has been added successfully!')
            return redirect('books:book_detail', pk=book.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = NewBook_form()
    
    return render(request, "books/register_a_book.html", {'form': form})


class SearchResultsView(ListView):
    model = Book
    template_name = "books/search_results.html"
    context_object_name = 'books'
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            from django.db.models import Case, When, IntegerField, Value
            
            # Clean and prepare search query
            query = query.strip()
            search_terms = query.split()
            
            # Exact phrase matching (highest priority)
            exact_match = (
                Q(title__iexact=query) |
                Q(author__iexact=query)
            )
            
            # Title and author get higher priority
            high_priority = (
                Q(title__icontains=query) |
                Q(author__icontains=query)
            )
            
            # Medium priority fields
            medium_priority = (
                Q(series__icontains=query) |
                Q(publisher__icontains=query) |
                Q(keywords__icontains=query)
            )
            
            # Lower priority fields
            low_priority = (
                Q(isbn__icontains=query) |
                Q(barcode__icontains=query) |
                Q(editor__icontains=query) |
                Q(translator__icontains=query) |
                Q(book_summary__icontains=query)
            )
            
            # Multi-word search with AND logic
            multi_word_filter = Q()
            if len(search_terms) > 1:
                for term in search_terms:
                    term_filter = (
                        Q(title__icontains=term) |
                        Q(author__icontains=term) |
                        Q(keywords__icontains=term) |
                        Q(series__icontains=term) |
                        Q(publisher__icontains=term)
                    )
                    multi_word_filter &= term_filter
            
            # Starts with matching for better relevance
            starts_with = (
                Q(title__istartswith=query) |
                Q(author__istartswith=query)
            )
            
            # Combine all filters
            combined_filter = (
                exact_match | high_priority | medium_priority | 
                low_priority | multi_word_filter | starts_with
            )
            
            # Apply search filter and add relevance scoring
            queryset = Book.objects.filter(combined_filter).annotate(
                relevance_score=Case(
                    # Exact matches get highest score
                    When(Q(title__iexact=query) | Q(author__iexact=query), then=Value(100)),
                    # Starts with gets high score
                    When(Q(title__istartswith=query) | Q(author__istartswith=query), then=Value(90)),
                    # Title/author contains gets medium-high score
                    When(Q(title__icontains=query) | Q(author__icontains=query), then=Value(80)),
                    # Series/publisher gets medium score
                    When(Q(series__icontains=query) | Q(publisher__icontains=query), then=Value(60)),
                    # Other fields get lower score
                    default=Value(40),
                    output_field=IntegerField()
                )
            ).order_by('-relevance_score', 'title').distinct()
            
            return queryset
        return Book.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


@login_required
def borrow_book(request, book_id):
    """Submit a borrow request for a book"""
    book = get_object_or_404(Book, id=book_id)
    user_profile = get_object_or_404(UserProfileinfo, user=request.user)
    
    if not book.is_available:
        messages.error(request, 'This book is not available for borrowing.')
        return redirect('books:book_detail', pk=book.pk)
    
    # Check if user already has a pending request for this book
    existing_request = BorrowRequest.objects.filter(
        book=book,
        requester=user_profile,
        status='pending'
    ).first()
    
    if existing_request:
        messages.warning(request, f'You already have a pending request for "{book.title}".')
        return redirect('books:book_detail', pk=book.pk)
    
    if request.method == 'POST':
        duration_days = int(request.POST.get('duration_days', 14))
        notes = request.POST.get('notes', '')
        
        # Create borrow request
        borrow_request = BorrowRequest.objects.create(
            book=book,
            requester=user_profile,
            requested_duration_days=duration_days,
            notes=notes,
            status='pending'
        )
        
        messages.success(request, f'Your borrow request for "{book.title}" has been submitted and is pending approval from a librarian.')
        return redirect('books:book_detail', pk=book.pk)
    
    # If GET request, show the borrow request form
    context = {
        'book': book,
        'user_profile': user_profile,
    }
    return render(request, 'books/borrow_request_form.html', context)


@librarian_required
def manage_borrow_requests(request):
    """View for librarians to manage borrow and return requests"""
    # Borrow requests
    pending_borrow_requests = BorrowRequest.objects.filter(status='pending').order_by('-request_date')
    processed_borrow_requests = BorrowRequest.objects.exclude(status='pending').order_by('-processed_date')[:20]
    
    # Return requests
    pending_return_requests = ReturnRequest.objects.filter(status='pending').order_by('-request_date')
    processed_return_requests = ReturnRequest.objects.exclude(status='pending').order_by('-processed_date')[:20]
    
    context = {
        'pending_borrow_requests': pending_borrow_requests,
        'processed_borrow_requests': processed_borrow_requests,
        'pending_return_requests': pending_return_requests,
        'processed_return_requests': processed_return_requests,
        # Legacy context for backward compatibility
        'pending_requests': pending_borrow_requests,
        'processed_requests': processed_borrow_requests,
    }
    return render(request, 'books/manage_borrow_requests.html', context)


@librarian_required
def approve_borrow_request(request, request_id):
    """Approve a borrow request and create actual borrowing"""
    borrow_request = get_object_or_404(BorrowRequest, id=request_id, status='pending')
    
    if request.method == 'POST':
        admin_notes = request.POST.get('admin_notes', '')
        
        # Check if book is still available
        if not borrow_request.book.is_available:
            messages.error(request, f'Book "{borrow_request.book.title}" is no longer available.')
            return redirect('books:manage_borrow_requests')
        
        # Create actual borrowing record
        due_date = date.today() + timedelta(days=borrow_request.requested_duration_days)
        borrowing = Borrower.objects.create(
            book=borrow_request.book,
            borrower=borrow_request.requester,
            due_date=due_date,
            status='borrowed'
        )
        
        # Update book availability
        borrow_request.book.is_available = False
        borrow_request.book.save()
        
        # Update user's current books count
        borrow_request.requester.current_books_count += 1
        borrow_request.requester.save()
        
        # Update request status
        borrow_request.status = 'approved'
        borrow_request.admin_notes = admin_notes
        
        # Handle users without UserProfileinfo (like superusers)
        try:
            borrow_request.processed_by = request.user.userprofileinfo
        except UserProfileinfo.DoesNotExist:
            # For superusers or users without profiles, create a minimal profile or set to None
            borrow_request.processed_by = None
        
        borrow_request.processed_date = timezone.now()
        borrow_request.save()
        
        messages.success(request, f'Borrow request approved. "{borrow_request.book.title}" has been borrowed by {borrow_request.requester.user.username}.')
        return redirect('books:manage_borrow_requests')
    
    context = {
        'borrow_request': borrow_request,
        'action': 'approve'
    }
    return render(request, 'books/process_borrow_request.html', context)


@librarian_required
def approve_return_request(request, request_id):
    """Approve a return request and process the actual return"""
    return_request = get_object_or_404(ReturnRequest, id=request_id, status='pending')
    
    if request.method == 'POST':
        admin_notes = request.POST.get('admin_notes', '')
        
        # Check if borrowing is still valid
        if return_request.borrowing.status != 'borrowed':
            messages.error(request, f'Book "{return_request.borrowing.book.title}" has already been returned.')
            return redirect('books:manage_borrow_requests')
        
        # Process the actual return
        borrowing = return_request.borrowing
        borrowing.return_date = date.today()
        borrowing.status = 'returned'
        
        # Calculate fine if overdue
        if borrowing.is_overdue:
            fine = borrowing.calculate_fine()
            borrowing.fine_amount = fine
            borrowing.borrower.total_fines += fine
            borrowing.borrower.save()
        
        borrowing.save()
        
        # Update book and user status
        borrowing.book.is_available = True
        borrowing.book.save()
        
        # Safely decrement current_books_count
        if borrowing.borrower.current_books_count > 0:
            borrowing.borrower.current_books_count -= 1
            borrowing.borrower.save()
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"User {borrowing.borrower.user.username} current_books_count is already 0 when returning book {borrowing.book.title}")
            borrowing.borrower.current_books_count = 0
            borrowing.borrower.save()
        
        # Update return request status
        return_request.status = 'approved'
        return_request.admin_notes = admin_notes
        
        # Handle users without UserProfileinfo (like superusers)
        try:
            return_request.processed_by = request.user.userprofileinfo
        except UserProfileinfo.DoesNotExist:
            return_request.processed_by = None
        
        return_request.processed_date = timezone.now()
        return_request.save()
        
        # Send return confirmation email
        try:
            send_return_confirmation.delay(borrowing.id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to queue return confirmation email: {str(e)}")
        
        # Check for reservations and notify users
        active_reservations = BookReservation.objects.filter(
            book=borrowing.book,
            status='active'
        ).order_by('reservation_date')
        
        if active_reservations.exists():
            first_reservation = active_reservations.first()
            try:
                send_reservation_available_notification.delay(first_reservation.id)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to queue reservation notification email: {str(e)}")
        
        messages.success(request, f'Return request approved. "{borrowing.book.title}" has been returned by {borrowing.borrower.user.username}.')
        return redirect('books:manage_borrow_requests')
    
    context = {
        'return_request': return_request,
        'action': 'approve',
        'today': date.today()
    }
    return render(request, 'books/process_return_request.html', context)


@librarian_required
def deny_return_request(request, request_id):
    """Deny a return request"""
    return_request = get_object_or_404(ReturnRequest, id=request_id, status='pending')
    
    if request.method == 'POST':
        admin_notes = request.POST.get('admin_notes', '')
        
        # Update return request status
        return_request.status = 'denied'
        return_request.admin_notes = admin_notes
        
        # Handle users without UserProfileinfo (like superusers)
        try:
            return_request.processed_by = request.user.userprofileinfo
        except UserProfileinfo.DoesNotExist:
            return_request.processed_by = None
        
        return_request.processed_date = timezone.now()
        return_request.save()
        
        messages.success(request, f'Return request denied for "{return_request.borrowing.book.title}".')
        return redirect('books:manage_borrow_requests')
    
    context = {
        'return_request': return_request,
        'action': 'deny',
        'today': date.today()
    }
    return render(request, 'books/process_return_request.html', context)


@librarian_required
def deny_borrow_request(request, request_id):
    """Deny a borrow request"""
    borrow_request = get_object_or_404(BorrowRequest, id=request_id, status='pending')
    
    if request.method == 'POST':
        admin_notes = request.POST.get('admin_notes', '')
        
        # Update request status
        borrow_request.status = 'denied'
        borrow_request.admin_notes = admin_notes
        
        # Handle users without UserProfileinfo (like superusers)
        try:
            borrow_request.processed_by = request.user.userprofileinfo
        except UserProfileinfo.DoesNotExist:
            # For superusers or users without profiles, create a minimal profile or set to None
            borrow_request.processed_by = None
        
        borrow_request.processed_date = timezone.now()
        borrow_request.save()
        
        messages.success(request, f'Borrow request denied for "{borrow_request.book.title}".')
        return redirect('books:manage_borrow_requests')
    
    context = {
        'borrow_request': borrow_request,
        'action': 'deny'
    }
    return render(request, 'books/process_borrow_request.html', context)


@login_required
def return_book(request, borrowing_id):
    """Submit a return request for a borrowed book"""
    borrowing = get_object_or_404(Borrower, id=borrowing_id, borrower__user=request.user)
    user_profile = get_object_or_404(UserProfileinfo, user=request.user)
    
    if borrowing.status != 'borrowed':
        messages.error(request, 'This book has already been returned or has a pending return request.')
        return redirect('books:book_detail', pk=borrowing.book.pk)
    
    # Check if user already has a pending return request for this borrowing
    existing_request = ReturnRequest.objects.filter(
        borrowing=borrowing,
        requester=user_profile,
        status='pending'
    ).first()
    
    if existing_request:
        messages.warning(request, f'You already have a pending return request for "{borrowing.book.title}".')
        return redirect('books:book_detail', pk=borrowing.book.pk)
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        
        # Create return request
        return_request = ReturnRequest.objects.create(
            borrowing=borrowing,
            requester=user_profile,
            notes=notes,
            status='pending'
        )
        
        messages.success(request, f'Your return request for "{borrowing.book.title}" has been submitted and is pending approval from a librarian.')
        return redirect('books:book_detail', pk=borrowing.book.pk)
    
    # If GET request, show the return request form
    context = {
        'borrowing': borrowing,
        'user_profile': user_profile,
    }
    return render(request, 'books/return_request_form.html', context)


@login_required
def process_return_directly(request, borrowing_id):
    """Direct return processing (for admin use or legacy support)"""
    borrowing = get_object_or_404(Borrower, id=borrowing_id)
    
    if borrowing.status != 'borrowed':
        messages.error(request, 'This book has already been returned.')
        return redirect('books:book_detail', pk=borrowing.book.pk)
    
    # Update borrowing record
    borrowing.return_date = date.today()
    borrowing.status = 'returned'
    
    # Calculate fine if overdue
    if borrowing.is_overdue:
        fine = borrowing.calculate_fine()
        borrowing.fine_amount = fine
        borrowing.borrower.total_fines += fine
        borrowing.borrower.save()
        messages.warning(request, f'Book returned with a fine of ${fine:.2f} for being overdue.')
    
    borrowing.save()
    
    # Update book and user status
    borrowing.book.is_available = True
    borrowing.book.save()
    
    # Safely decrement current_books_count (prevent negative values)
    if borrowing.borrower.current_books_count > 0:
        borrowing.borrower.current_books_count -= 1
        borrowing.borrower.save()
    else:
        # Log this issue as it indicates data inconsistency
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"User {borrowing.borrower.user.username} current_books_count is already 0 when returning book {borrowing.book.title}")
        # Reset to 0 to ensure consistency
        borrowing.borrower.current_books_count = 0
        borrowing.borrower.save()
    
    # Send return confirmation email
    try:
        send_return_confirmation.delay(borrowing.id)
    except Exception as e:
        # Log error but don't fail the return process
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to queue return confirmation email: {str(e)}")
    
    # Check for reservations and notify users
    active_reservations = BookReservation.objects.filter(
        book=borrowing.book,
        status='active'
    ).order_by('reservation_date')
    
    if active_reservations.exists():
        # Fulfill the first reservation
        first_reservation = active_reservations.first()
        first_reservation.status = 'fulfilled'
        first_reservation.save()
        
        # Send notification to the user
        try:
            send_reservation_available_notification.delay(first_reservation.id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to queue reservation notification: {str(e)}")
    
    messages.success(request, f'You have successfully returned "{borrowing.book.title}".')
    return redirect('books:book_detail', pk=borrowing.book.pk)


@login_required
def reserve_book(request, book_id):
    """Reserve a book"""
    book = get_object_or_404(Book, id=book_id)
    user_profile = get_object_or_404(UserProfileinfo, user=request.user)
    
    if book.is_available:
        messages.error(request, 'This book is available for borrowing. No need to reserve.')
        return redirect('books:book_detail', pk=book.pk)
    
    # Check if user already has a reservation for this book
    existing_reservation = BookReservation.objects.filter(
        book=book, user=user_profile, status='active'
    ).exists()
    
    if existing_reservation:
        messages.error(request, 'You already have an active reservation for this book.')
        return redirect('books:book_detail', pk=book.pk)
    
    # Create reservation
    expiry_date = date.today() + timedelta(days=7)  # Reservation expires in 7 days
    reservation = BookReservation.objects.create(
        book=book,
        user=user_profile,
        expiry_date=expiry_date,
        status='active'
    )
    
    messages.success(request, f'You have successfully reserved "{book.title}". You will be notified when it becomes available.')
    return redirect('books:book_detail', pk=book.pk)


@login_required
def my_books(request):
    """Display user's borrowed books, reservations, and borrow requests"""
    user_profile = get_object_or_404(UserProfileinfo, user=request.user)
    
    borrowed_books = Borrower.objects.filter(
        borrower=user_profile, 
        status='borrowed'
    ).select_related('book')
    
    reservations = BookReservation.objects.filter(
        user=user_profile, 
        status='active'
    ).select_related('book')
    
    # Get borrow requests
    pending_requests = BorrowRequest.objects.filter(
        requester=user_profile,
        status='pending'
    ).select_related('book')
    
    processed_requests = BorrowRequest.objects.filter(
        requester=user_profile,
        status__in=['approved', 'denied']
    ).select_related('book', 'processed_by').order_by('-processed_date')[:10]
    
    # Calculate overdue count
    overdue_count = borrowed_books.filter(due_date__lt=date.today()).count()
    
    context = {
        'current_borrowings': borrowed_books,
        'reservations': reservations,
        'pending_requests': pending_requests,
        'processed_requests': processed_requests,
        'borrowing_history': borrowed_books,  # For compatibility with template
        'overdue_count': overdue_count,
        'user_profile': user_profile,
    }
    
    return render(request, 'books/my_books.html', context)


@login_required
def barcode_scan(request):
    """Barcode scanning interface for quick book operations"""
    form = BarcodeScanForm()
    book = None
    error_message = None
    
    if request.method == 'POST':
        form = BarcodeScanForm(request.POST)
        if form.is_valid():
            barcode = form.cleaned_data['barcode']
            try:
                book = Book.objects.get(barcode=barcode)
            except Book.DoesNotExist:
                error_message = f"No book found with barcode: {barcode}"
    
    context = {
        'form': form,
        'book': book,
        'error_message': error_message,
    }
    
    return render(request, 'books/barcode_scan.html', context)


@login_required
def barcode_lookup_api(request):
    """API endpoint for barcode lookup"""
    if request.method == 'GET':
        barcode = request.GET.get('barcode')
        if barcode:
            try:
                book = Book.objects.get(barcode=barcode)
                data = {
                    'success': True,
                    'book': {
                        'id': book.id,
                        'title': book.title,
                        'author': book.author,
                        'isbn': book.isbn,
                        'barcode': book.barcode,
                        'is_available': book.is_available,
                        'cover_image_url': book.get_cover_image_url(),
                    }
                }
            except Book.DoesNotExist:
                data = {
                    'success': False,
                    'error': f'No book found with barcode: {barcode}'
                }
        else:
            data = {
                'success': False,
                'error': 'Barcode parameter is required'
            }
        
        return JsonResponse(data)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def quick_borrow(request, book_id):
    """Quick borrow functionality for barcode scanning"""
    book = get_object_or_404(Book, id=book_id)
    
    if not book.is_available:
        messages.error(request, f'Book "{book.title}" is not available for borrowing.')
        return redirect('books:barcode_scan')
    
    # Get or create user profile
    user_profile, created = UserProfileinfo.objects.get_or_create(
        user=request.user,
        defaults={'status': 'active'}
    )
    
    # Create borrowing record
    due_date = date.today() + timedelta(days=14)  # 2 weeks borrowing period
    
    borrowing = Borrower.objects.create(
        book=book,
        borrower=user_profile,
        due_date=due_date,
        status='borrowed'
    )
    
    # Update book availability
    book.is_available = False
    book.save()
    
    # Send confirmation email
    try:
        send_return_confirmation.delay(
            user_email=request.user.email,
            user_name=request.user.get_full_name() or request.user.username,
            book_title=book.title,
            book_author=book.author,
            due_date=due_date.strftime('%Y-%m-%d')
        )
    except Exception as e:
        # Log error but don't fail the borrowing process
        print(f"Email notification error: {e}")
    
    messages.success(request, f'Successfully borrowed "{book.title}". Due date: {due_date.strftime("%B %d, %Y")}')
    return redirect('books:barcode_scan')

