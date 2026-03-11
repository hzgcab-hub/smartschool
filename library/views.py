from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from .models import (
    Book, BookCategory, BookAuthor, BookPublisher,
    BookIssue, BookReservation, BookRequest,
    LibraryCard, LibrarySetting
)
from .forms import (
    BookForm, BookIssueForm, BookReturnForm, BookReservationForm,
    BookRequestForm, LibraryCardForm, BookSearchForm
)
from students.models import Student
from teachers.models import Teacher

# ========== Dashboard ==========
@login_required
def library_dashboard(request):
    """Library dashboard with statistics"""
    today = date.today()
    
    # Statistics
    total_books = Book.objects.filter(is_active=True).count()
    available_books = Book.objects.filter(status='available', is_active=True).count()
    issued_books = BookIssue.objects.filter(status__in=['issued', 'overdue']).count()
    overdue_books = BookIssue.objects.filter(status='overdue').count()
    
    # Recent activities
    recent_issues = BookIssue.objects.select_related('book', 'student', 'teacher').order_by('-issue_date')[:10]
    popular_books = Book.objects.annotate(
        issue_count=Count('issues')
    ).order_by('-issue_count')[:5]
    
    # Books due today/tomorrow
    due_today = BookIssue.objects.filter(
        due_date=today,
        status__in=['issued', 'overdue']
    ).count()
    
    due_tomorrow = BookIssue.objects.filter(
        due_date=today + timedelta(days=1),
        status__in=['issued', 'overdue']
    ).count()
    
    context = {
        'total_books': total_books,
        'available_books': available_books,
        'issued_books': issued_books,
        'overdue_books': overdue_books,
        'recent_issues': recent_issues,
        'popular_books': popular_books,
        'due_today': due_today,
        'due_tomorrow': due_tomorrow,
    }
    return render(request, 'library/dashboard.html', context)


# ========== Book Management ==========
@login_required
def book_list(request):
    """List all books with search and filters"""
    books = Book.objects.filter(is_active=True).select_related('category', 'publisher')
    
    # Search form
    form = BookSearchForm(request.GET)
    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        language = form.cleaned_data.get('language')
        status = form.cleaned_data.get('status')
        
        if query:
            books = books.filter(
                Q(title__icontains=query) |
                Q(isbn__icontains=query) |
                Q(accession_number__icontains=query) |
                Q(authors__first_name__icontains=query) |
                Q(authors__last_name__icontains=query)
            ).distinct()
        
        if category:
            books = books.filter(category=category)
        
        if language:
            books = books.filter(language=language)
        
        if status:
            books = books.filter(status=status)
    
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
    }
    return render(request, 'library/book_list.html', context)

@login_required
def book_detail(request, pk):
    """View book details"""
    book = get_object_or_404(Book, pk=pk)
    issues = book.issues.all().order_by('-issue_date')[:10]
    reservations = book.reservations.filter(status='pending')
    
    context = {
        'book': book,
        'issues': issues,
        'reservations': reservations,
    }
    return render(request, 'library/book_detail.html', context)

@login_required
def book_add(request):
    """Add new book"""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" added successfully!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm()
    
    context = {
        'form': form,
        'title': 'Add New Book'
    }
    return render(request, 'library/book_form.html', context)

@login_required
def book_edit(request, pk):
    """Edit book"""
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save()
            messages.success(request, 'Book updated successfully!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
    
    context = {
        'form': form,
        'title': f'Edit {book.title}'
    }
    return render(request, 'library/book_form.html', context)

@login_required
def book_delete(request, pk):
    """Delete book (soft delete)"""
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        book.is_active = False
        book.save()
        messages.success(request, 'Book deleted successfully!')
        return redirect('book_list')
    
    context = {'book': book}
    return render(request, 'library/book_confirm_delete.html', context)


# ========== Issue/Return Management ==========
@login_required
def issue_list(request):
    """List all book issues"""
    issues = BookIssue.objects.select_related('book', 'student', 'teacher').order_by('-issue_date')
    
    # Filters
    status = request.GET.get('status')
    if status:
        issues = issues.filter(status=status)
    
    # Search
    query = request.GET.get('q')
    if query:
        issues = issues.filter(
            Q(book__title__icontains=query) |
            Q(book__isbn__icontains=query) |
            Q(student__user__first_name__icontains=query) |
            Q(teacher__user__first_name__icontains=query)
        )
    
    paginator = Paginator(issues, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
        'query': query,
    }
    return render(request, 'library/issue_list.html', context)

@login_required
def issue_detail(request, pk):
    """View issue details"""
    issue = get_object_or_404(BookIssue, pk=pk)
    
    context = {
        'issue': issue,
    }
    return render(request, 'library/issue_detail.html', context)

@login_required
def issue_book(request):
    """Issue a book to student/teacher"""
    if request.method == 'POST':
        form = BookIssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.issued_by = request.user
            
            # Set borrower
            borrower_type = form.cleaned_data['borrower_type']
            if borrower_type == 'student':
                issue.student = form.cleaned_data['student']
            else:
                issue.teacher = form.cleaned_data['teacher']
            
            # Update book available copies
            book = issue.book
            book.available_copies -= 1
            if book.available_copies == 0:
                book.status = 'issued'
            book.save()
            
            issue.save()
            messages.success(request, f'Book "{book.title}" issued successfully!')
            return redirect('issue_detail', pk=issue.pk)
    else:
        form = BookIssueForm()
    
    context = {
        'form': form,
        'title': 'Issue Book'
    }
    return render(request, 'library/issue_form.html', context)

@login_required
def return_book(request):
    """Return a book"""
    if request.method == 'POST':
        form = BookReturnForm(request.POST)
        if form.is_valid():
            issue = form.cleaned_data['issue']
            condition = form.cleaned_data['condition']
            fine_paid = form.cleaned_data['fine_paid']
            remarks = form.cleaned_data['remarks']
            
            # Update issue
            issue.return_date = date.today()
            issue.received_by = request.user
            issue.remarks = remarks
            
            # Update based on condition
            if condition == 'damaged':
                issue.status = 'damaged'
                issue.book.status = 'damaged'
                messages.warning(request, 'Book marked as damaged.')
            elif condition == 'lost':
                issue.status = 'lost'
                issue.book.status = 'lost'
                messages.warning(request, 'Book marked as lost.')
            else:
                issue.status = 'returned'
                issue.book.available_copies += 1
                if issue.book.available_copies > 0:
                    issue.book.status = 'available'
                messages.success(request, 'Book returned successfully!')
            
            # Calculate and handle fine
            if issue.fine_amount > 0:
                issue.fine_paid = fine_paid
                if fine_paid:
                    issue.fine_paid_date = date.today()
                    messages.info(request, f'Fine of ETB {issue.fine_amount} paid.')
            
            issue.book.save()
            issue.save()
            
            return redirect('issue_detail', pk=issue.pk)
    else:
        form = BookReturnForm()
    
    context = {
        'form': form,
        'title': 'Return Book'
    }
    return render(request, 'library/return_form.html', context)

@login_required
def renew_book(request, pk):
    """Renew a book issue"""
    issue = get_object_or_404(BookIssue, pk=pk, status__in=['issued', 'overdue'])
    
    if request.method == 'POST':
        new_due_date = request.POST.get('new_due_date')
        if new_due_date:
            issue.due_date = new_due_date
            issue.status = 'issued'
            issue.save()
            messages.success(request, f'Book renewed. New due date: {new_due_date}')
            return redirect('issue_detail', pk=issue.pk)
    
    context = {
        'issue': issue,
        'max_days': 14,  # Can be from settings
    }
    return render(request, 'library/renew_form.html', context)


# ========== Reservations ==========
@login_required
def reservation_list(request):
    """List all reservations"""
    reservations = BookReservation.objects.select_related('book', 'student', 'teacher').order_by('-reservation_date')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        reservations = reservations.filter(status=status)
    
    paginator = Paginator(reservations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
    }
    return render(request, 'library/reservation_list.html', context)

@login_required
def create_reservation(request):
    """Create a new reservation"""
    if request.method == 'POST':
        form = BookReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            
            # Set borrower
            borrower_type = form.cleaned_data['borrower_type']
            if borrower_type == 'student':
                reservation.student = form.cleaned_data['student']
            else:
                reservation.teacher = form.cleaned_data['teacher']
            
            # Set expiry date (default 3 days from now)
            settings = LibrarySetting.objects.first()
            expiry_days = settings.reservation_expiry_days if settings else 3
            reservation.expiry_date = date.today() + timedelta(days=expiry_days)
            
            reservation.save()
            messages.success(request, 'Book reserved successfully!')
            return redirect('reservation_list')
    else:
        form = BookReservationForm()
    
    context = {
        'form': form,
        'title': 'Reserve Book'
    }
    return render(request, 'library/reservation_form.html', context)

@login_required
def cancel_reservation(request, pk):
    """Cancel a reservation"""
    reservation = get_object_or_404(BookReservation, pk=pk, status='pending')
    
    if request.method == 'POST':
        reservation.status = 'cancelled'
        reservation.save()
        messages.success(request, 'Reservation cancelled successfully!')
        return redirect('reservation_list')
    
    context = {'reservation': reservation}
    return render(request, 'library/reservation_confirm_cancel.html', context)


# ========== Book Requests ==========
@login_required
def request_list(request):
    """List all book requests"""
    requests = BookRequest.objects.select_related('user').order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        requests = requests.filter(status=status)
    
    paginator = Paginator(requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
    }
    return render(request, 'library/request_list.html', context)

@login_required
def request_detail(request, pk):
    """View request details"""
    book_request = get_object_or_404(BookRequest, pk=pk)
    
    context = {
        'request': book_request,
    }
    return render(request, 'library/request_detail.html', context)

@login_required
def create_request(request):
    """Create a new book request"""
    if request.method == 'POST':
        form = BookRequestForm(request.POST)
        if form.is_valid():
            book_request = form.save(commit=False)
            book_request.user = request.user
            book_request.save()
            messages.success(request, 'Book request submitted successfully!')
            return redirect('request_list')
    else:
        form = BookRequestForm()
    
    context = {
        'form': form,
        'title': 'Request New Book'
    }
    return render(request, 'library/request_form.html', context)


# ========== Categories ==========
@login_required
def category_list(request):
    """List all book categories"""
    categories = BookCategory.objects.annotate(
        book_count=Count('books')
    ).order_by('name')
    
    context = {
        'categories': categories,
    }
    return render(request, 'library/category_list.html', context)

@login_required
def category_add(request):
    """Add new category"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if name:
            category = BookCategory.objects.create(
                name=name,
                description=description
            )
            messages.success(request, f'Category "{name}" added successfully!')
            return redirect('category_list')
    
    return render(request, 'library/category_form.html')


# ========== Authors ==========
@login_required
def author_list(request):
    """List all authors"""
    authors = BookAuthor.objects.annotate(
        book_count=Count('books')
    ).order_by('last_name', 'first_name')
    
    context = {
        'authors': authors,
    }
    return render(request, 'library/author_list.html', context)

@login_required
def author_add(request):
    """Add new author"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        biography = request.POST.get('biography')
        
        if first_name and last_name:
            author = BookAuthor.objects.create(
                first_name=first_name,
                last_name=last_name,
                biography=biography
            )
            messages.success(request, f'Author "{author.full_name}" added successfully!')
            return redirect('author_list')
    
    return render(request, 'library/author_form.html')


# ========== Library Cards ==========
@login_required
def card_list(request):
    """List all library cards"""
    cards = LibraryCard.objects.select_related('student', 'teacher').order_by('-issued_date')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        cards = cards.filter(status=status)
    
    # Search
    query = request.GET.get('q')
    if query:
        cards = cards.filter(
            Q(card_number__icontains=query) |
            Q(student__user__first_name__icontains=query) |
            Q(teacher__user__first_name__icontains=query)
        )
    
    paginator = Paginator(cards, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
        'query': query,
    }
    return render(request, 'library/card_list.html', context)

@login_required
def card_detail(request, pk):
    """View card details"""
    card = get_object_or_404(LibraryCard, pk=pk)
    
    # Get active issues
    if card.student:
        active_issues = BookIssue.objects.filter(
            student=card.student,
            status__in=['issued', 'overdue']
        )
    else:
        active_issues = BookIssue.objects.filter(
            teacher=card.teacher,
            status__in=['issued', 'overdue']
        )
    
    context = {
        'card': card,
        'active_issues': active_issues,
    }
    return render(request, 'library/card_detail.html', context)

@login_required
def card_create(request):
    """Create new library card"""
    if request.method == 'POST':
        form = LibraryCardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.issued_by = request.user
            
            # Set owner
            card_type = form.cleaned_data['card_type']
            if card_type == 'student':
                card.student = form.cleaned_data['student']
            else:
                card.teacher = form.cleaned_data['teacher']
            
            card.save()
            messages.success(request, f'Library card created successfully! Card number: {card.card_number}')
            return redirect('card_detail', pk=card.pk)
    else:
        form = LibraryCardForm()
    
    context = {
        'form': form,
        'title': 'Create Library Card'
    }
    return render(request, 'library/card_form.html', context)


# ========== Reports ==========
@login_required
def library_reports(request):
    """Library reports"""
    report_type = request.GET.get('type', 'overview')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 30 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    context = {
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    if report_type == 'overview':
        # Overview statistics
        context.update({
            'total_books': Book.objects.filter(is_active=True).count(),
            'total_issues': BookIssue.objects.filter(
                issue_date__gte=start_date,
                issue_date__lte=end_date
            ).count(),
            'total_returns': BookIssue.objects.filter(
                return_date__gte=start_date,
                return_date__lte=end_date
            ).count(),
            'total_fines': BookIssue.objects.filter(
                return_date__gte=start_date,
                return_date__lte=end_date
            ).aggregate(Sum('fine_amount'))['fine_amount__sum'] or 0,
        })
    
    elif report_type == 'popular':
        # Popular books
        context['popular_books'] = Book.objects.annotate(
            issue_count=Count('issues')
        ).filter(
            issues__issue_date__gte=start_date,
            issues__issue_date__lte=end_date
        ).order_by('-issue_count')[:20]
    
    elif report_type == 'overdue':
        # Overdue books
        context['overdue_books'] = BookIssue.objects.filter(
            status='overdue',
            due_date__gte=start_date,
            due_date__lte=end_date
        ).select_related('book', 'student', 'teacher')
    
    elif report_type == 'category':
        # Category-wise distribution
        context['category_stats'] = BookCategory.objects.annotate(
            book_count=Count('books')
        ).filter(book_count__gt=0)
    
    return render(request, 'library/reports.html', context)