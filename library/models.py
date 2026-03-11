from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import User
from students.models import Student
from teachers.models import Teacher
from datetime import date, timedelta

class BookCategory(models.Model):
    """Book categories/genres"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Book Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class BookPublisher(models.Model):
    """Book publishers"""
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class BookAuthor(models.Model):
    """Book authors"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    biography = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    death_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Book(models.Model):
    """Library books"""
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('am', 'Amharic'),
        ('om', 'Oromo'),
        ('ti', 'Tigrinya'),
        ('so', 'Somali'),
        ('fr', 'French'),
        ('ar', 'Arabic'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('issued', 'Issued'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
        ('maintenance', 'Under Maintenance'),
    )
    
    # Basic Information
    title = models.CharField(max_length=300)
    isbn = models.CharField(max_length=20, unique=True, verbose_name="ISBN")
    authors = models.ManyToManyField(BookAuthor, related_name='books')
    category = models.ForeignKey(BookCategory, on_delete=models.SET_NULL, null=True, related_name='books')
    publisher = models.ForeignKey(BookPublisher, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    
    # Publication Details
    publication_year = models.IntegerField(null=True, blank=True)
    edition = models.CharField(max_length=50, blank=True)
    volume = models.CharField(max_length=50, blank=True)
    pages = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    
    # Library Details
    accession_number = models.CharField(max_length=50, unique=True)
    shelf_location = models.CharField(max_length=50, blank=True)
    rack_number = models.CharField(max_length=20, blank=True)
    
    # Copies
    total_copies = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    available_copies = models.IntegerField(default=1)
    
    # Additional Info
    description = models.TextField(blank=True)
    keywords = models.CharField(max_length=500, blank=True, help_text="Comma-separated keywords")
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    late_fee_per_day = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['title']
    
    def __str__(self):
        return f"{self.title} ({self.isbn})"
    
    def save(self, *args, **kwargs):
        if not self.accession_number:
            # Generate accession number: ACC/YYYY/XXXX
            year = date.today().year
            last_book = Book.objects.filter(accession_number__startswith=f"ACC/{year}/").order_by('id').last()
            if last_book:
                last_number = int(last_book.accession_number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1001
            self.accession_number = f"ACC/{year}/{new_number:04d}"
        
        # Ensure available_copies doesn't exceed total_copies
        if self.available_copies > self.total_copies:
            self.available_copies = self.total_copies
        
        super().save(*args, **kwargs)
    
    def is_available(self):
        return self.available_copies > 0 and self.status == 'available'


class BookIssue(models.Model):
    """Book borrowing records"""
    STATUS_CHOICES = (
        ('issued', 'Issued'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    )
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issues')
    
    # Can be issued to either student or teacher
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='book_issues')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True, related_name='book_issues')
    
    # Issue details
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='issued')
    
    # Fine
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    fine_paid = models.BooleanField(default=False)
    fine_paid_date = models.DateField(null=True, blank=True)
    
    # Tracking
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_books')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_books')
    
    # Remarks
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['status', 'due_date']),
        ]
    
    def __str__(self):
        borrower = self.student or self.teacher
        return f"{self.book.title} - {borrower} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Set due date if not provided (default 14 days from issue)
        if not self.due_date:
            self.due_date = date.today() + timedelta(days=14)
        
        # Calculate fine if overdue and returned
        if self.status == 'returned' and self.return_date and self.return_date > self.due_date:
            days_late = (self.return_date - self.due_date).days
            self.fine_amount = days_late * self.book.late_fee_per_day
        
        super().save(*args, **kwargs)
    
    def calculate_fine(self):
        """Calculate current fine for overdue books"""
        if self.status in ['issued', 'overdue'] and date.today() > self.due_date:
            days_late = (date.today() - self.due_date).days
            return days_late * self.book.late_fee_per_day
        return 0
    
    @property
    def borrower_name(self):
        if self.student:
            return f"{self.student.user.get_full_name()} (Student)"
        elif self.teacher:
            return f"{self.teacher.user.get_full_name()} (Teacher)"
        return "Unknown"
    
    @property
    def borrower_type(self):
        if self.student:
            return 'student'
        elif self.teacher:
            return 'teacher'
        return 'unknown'
    
    @property
    def borrower_id(self):
        if self.student:
            return self.student.id
        elif self.teacher:
            return self.teacher.id
        return None


class BookReservation(models.Model):
    """Book reservations"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('available', 'Available for Pickup'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    )
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='book_reservations')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True, related_name='book_reservations')
    
    reservation_date = models.DateField(auto_now_add=True)
    available_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    notified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-reservation_date']
        unique_together = ['book', 'student', 'teacher', 'status']
    
    def __str__(self):
        borrower = self.student or self.teacher
        return f"{self.book.title} - {borrower}"
    
    @property
    def borrower_name(self):
        if self.student:
            return f"{self.student.user.get_full_name()} (Student)"
        elif self.teacher:
            return f"{self.teacher.user.get_full_name()} (Teacher)"
        return "Unknown"


class BookRequest(models.Model):
    """Requests for new books"""
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('purchased', 'Purchased'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_requests')
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    reason = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Approval
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_book_requests')
    approved_date = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.author}"


class LibrarySetting(models.Model):
    """Library settings"""
    late_fee_per_day = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    max_books_per_student = models.IntegerField(default=3)
    max_books_per_teacher = models.IntegerField(default=5)
    loan_days_student = models.IntegerField(default=14)
    loan_days_teacher = models.IntegerField(default=30)
    reservation_expiry_days = models.IntegerField(default=3)
    enable_notifications = models.BooleanField(default=True)
    enable_reservations = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Library Settings"
    
    def __str__(self):
        return "Library Settings"


class LibraryCard(models.Model):
    """Library cards for students/teachers"""
    CARD_STATUS = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
        ('expired', 'Expired'),
    )
    
    card_number = models.CharField(max_length=50, unique=True)
    
    # Can be for either student or teacher
    student = models.OneToOneField(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='library_card')
    teacher = models.OneToOneField(Teacher, on_delete=models.CASCADE, null=True, blank=True, related_name='library_card')
    
    issued_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=CARD_STATUS, default='active')
    
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_library_cards')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        owner = self.student or self.teacher
        return f"Card {self.card_number} - {owner}"
    
    def save(self, *args, **kwargs):
        if not self.card_number:
            # Generate card number: LIB/YYYY/XXXX
            year = date.today().year
            last_card = LibraryCard.objects.filter(card_number__startswith=f"LIB/{year}/").order_by('id').last()
            if last_card:
                last_number = int(last_card.card_number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1001
            self.card_number = f"LIB/{year}/{new_number:04d}"
        
        # Set expiry date to 1 year from now if not set
        if not self.expiry_date:
            self.expiry_date = date.today() + timedelta(days=365)
        
        super().save(*args, **kwargs)
    
    @property
    def owner_name(self):
        if self.student:
            return self.student.user.get_full_name()
        elif self.teacher:
            return self.teacher.user.get_full_name()
        return "Unknown"
    
    @property
    def owner_type(self):
        if self.student:
            return 'student'
        elif self.teacher:
            return 'teacher'
        return 'unknown'
