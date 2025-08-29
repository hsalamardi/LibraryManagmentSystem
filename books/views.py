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
from .models import Book, Borrower, BookReservation
from library_users.models import UserProfileinfo
from .forms import NewBook_form, NewBorrower_form, BarcodeScanForm
from .email_notifications import EmailNotificationService
from .tasks import send_welcome_email, send_return_confirmation, send_reservation_available_notification


# Create your views here.

def landing(request):
    """Landing page with library statistics"""
    total_books = Book.objects.count()
    available_books = Book.objects.filter(is_available=True).count()
    borrowed_books = Borrower.objects.filter(status='borrowed').count()
    total_users = UserProfileinfo.objects.filter(status='active').count()
    
    context = {
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'total_users': total_users,
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
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(author__icontains=search_query) |
                Q(isbn__icontains=search_query) |
                Q(barcode__icontains=search_query) |
                Q(keywords__icontains=search_query)
            )
        
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
    context_object_name = 'book'
    
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
        
        return context

def books(request):
    """Simple books view - redirects to BooksListView"""
    return redirect('books:view_books_list')


@login_required(login_url='/library_users/register')
def form_name_view(request):
    """Add new book form"""
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
            return Book.objects.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(isbn__icontains=query) |
                Q(barcode__icontains=query) |
                Q(keywords__icontains=query)
            ).distinct()
        return Book.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


@login_required
def borrow_book(request, book_id):
    """Borrow a book"""
    book = get_object_or_404(Book, id=book_id)
    user_profile = get_object_or_404(UserProfileinfo, user=request.user)
    
    if not book.is_available:
        messages.error(request, 'This book is not available for borrowing.')
        return redirect('books:book_detail', pk=book.pk)
    
    if not user_profile.can_borrow_books:
        messages.error(request, 'You cannot borrow books at this time. Please check your account status.')
        return redirect('books:book_detail', pk=book.pk)
    
    # Create borrowing record
    due_date = date.today() + timedelta(days=14)  # 2 weeks borrowing period
    borrowing = Borrower.objects.create(
        book=book,
        borrower=user_profile,
        due_date=due_date,
        status='borrowed'
    )
    
    # Update book and user status
    book.is_available = False
    book.save()
    
    user_profile.current_books_count += 1
    user_profile.save()
    
    messages.success(request, f'You have successfully borrowed "{book.title}". Due date: {due_date}')
    return redirect('books:book_detail', pk=book.pk)


@login_required
def return_book(request, borrowing_id):
    """Return a borrowed book"""
    borrowing = get_object_or_404(Borrower, id=borrowing_id, borrower__user=request.user)
    
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
    
    borrowing.borrower.current_books_count -= 1
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
    """Display user's borrowed books and reservations"""
    user_profile = get_object_or_404(UserProfileinfo, user=request.user)
    
    borrowed_books = Borrower.objects.filter(
        borrower=user_profile, 
        status='borrowed'
    ).select_related('book')
    
    reservations = BookReservation.objects.filter(
        user=user_profile, 
        status='active'
    ).select_related('book')
    
    context = {
        'borrowed_books': borrowed_books,
        'reservations': reservations,
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

