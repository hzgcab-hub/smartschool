from django import forms
from .models import (
    Book, BookCategory, BookPublisher, BookAuthor,
    BookIssue, BookReservation, BookRequest, LibraryCard
)
from students.models import Student
from teachers.models import Teacher
from datetime import date, timedelta

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'isbn', 'authors', 'category', 'publisher',
            'publication_year', 'edition', 'volume', 'pages', 'language',
            'shelf_location', 'rack_number', 'total_copies', 'available_copies',
            'description', 'keywords', 'cover_image', 'price', 'late_fee_per_day',
            'status', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'keywords': forms.TextInput(attrs={'placeholder': 'Comma-separated keywords'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['authors'].required = True
        self.fields['category'].required = True
    
    def clean_isbn(self):
        isbn = self.cleaned_data['isbn']
        if Book.objects.filter(isbn=isbn).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('A book with this ISBN already exists.')
        return isbn
    
    def clean(self):
        cleaned_data = super().clean()
        total_copies = cleaned_data.get('total_copies')
        available_copies = cleaned_data.get('available_copies')
        
        if total_copies and available_copies and available_copies > total_copies:
            raise forms.ValidationError('Available copies cannot exceed total copies.')
        
        return cleaned_data


class BookIssueForm(forms.ModelForm):
    borrower_type = forms.ChoiceField(
        choices=[('student', 'Student'), ('teacher', 'Teacher')],
        widget=forms.RadioSelect,
        initial='student'
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'student-select'})
    )
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'teacher-select'})
    )
    
    class Meta:
        model = BookIssue
        fields = ['book', 'due_date', 'remarks']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['book'].queryset = Book.objects.filter(
            status='available',
            available_copies__gt=0,
            is_active=True
        )
        self.fields['due_date'].initial = date.today() + timedelta(days=14)
    
    def clean(self):
        cleaned_data = super().clean()
        borrower_type = cleaned_data.get('borrower_type')
        student = cleaned_data.get('student')
        teacher = cleaned_data.get('teacher')
        
        if borrower_type == 'student' and not student:
            raise forms.ValidationError('Please select a student.')
        if borrower_type == 'teacher' and not teacher:
            raise forms.ValidationError('Please select a teacher.')
        
        # Check if borrower has reached max books limit
        book = cleaned_data.get('book')
        if book and borrower_type == 'student' and student:
            current_issues = BookIssue.objects.filter(
                student=student,
                status__in=['issued', 'overdue']
            ).count()
            from .models import LibrarySetting
            settings = LibrarySetting.objects.first()
            max_books = settings.max_books_per_student if settings else 3
            
            if current_issues >= max_books:
                raise forms.ValidationError(f'Student has already reached maximum book limit ({max_books}).')
        
        elif book and borrower_type == 'teacher' and teacher:
            current_issues = BookIssue.objects.filter(
                teacher=teacher,
                status__in=['issued', 'overdue']
            ).count()
            from .models import LibrarySetting
            settings = LibrarySetting.objects.first()
            max_books = settings.max_books_per_teacher if settings else 5
            
            if current_issues >= max_books:
                raise forms.ValidationError(f'Teacher has already reached maximum book limit ({max_books}).')
        
        return cleaned_data


class BookReturnForm(forms.Form):
    issue = forms.ModelChoiceField(
        queryset=BookIssue.objects.filter(status__in=['issued', 'overdue']),
        label="Select Issue to Return"
    )
    condition = forms.ChoiceField(
        choices=[('good', 'Good'), ('damaged', 'Damaged'), ('lost', 'Lost')],
        initial='good'
    )
    fine_paid = forms.BooleanField(required=False, initial=True)
    remarks = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    def clean_issue(self):
        issue = self.cleaned_data['issue']
        if issue.status not in ['issued', 'overdue']:
            raise forms.ValidationError('This book is not currently issued.')
        return issue


class BookReservationForm(forms.ModelForm):
    borrower_type = forms.ChoiceField(
        choices=[('student', 'Student'), ('teacher', 'Teacher')],
        widget=forms.RadioSelect,
        initial='student'
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_active=True),
        required=False
    )
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.filter(is_active=True),
        required=False
    )
    
    class Meta:
        model = BookReservation
        fields = ['book', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['book'].queryset = Book.objects.filter(
            status='available',
            is_active=True
        )
    
    def clean(self):
        cleaned_data = super().clean()
        borrower_type = cleaned_data.get('borrower_type')
        student = cleaned_data.get('student')
        teacher = cleaned_data.get('teacher')
        book = cleaned_data.get('book')
        
        if borrower_type == 'student' and not student:
            raise forms.ValidationError('Please select a student.')
        if borrower_type == 'teacher' and not teacher:
            raise forms.ValidationError('Please select a teacher.')
        
        # Check if already reserved
        if book and borrower_type == 'student' and student:
            if BookReservation.objects.filter(
                book=book, student=student, status='pending'
            ).exists():
                raise forms.ValidationError('This book is already reserved by this student.')
        
        if book and borrower_type == 'teacher' and teacher:
            if BookReservation.objects.filter(
                book=book, teacher=teacher, status='pending'
            ).exists():
                raise forms.ValidationError('This book is already reserved by this teacher.')
        
        return cleaned_data


class BookRequestForm(forms.ModelForm):
    class Meta:
        model = BookRequest
        fields = ['title', 'author', 'isbn', 'publisher', 'reason', 'priority']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
        }


class LibraryCardForm(forms.ModelForm):
    card_type = forms.ChoiceField(
        choices=[('student', 'Student'), ('teacher', 'Teacher')],
        widget=forms.RadioSelect,
        initial='student'
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_active=True),
        required=False
    )
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.filter(is_active=True),
        required=False
    )
    
    class Meta:
        model = LibraryCard
        fields = ['expiry_date', 'status']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expiry_date'].initial = date.today() + timedelta(days=365)
    
    def clean(self):
        cleaned_data = super().clean()
        card_type = cleaned_data.get('card_type')
        student = cleaned_data.get('student')
        teacher = cleaned_data.get('teacher')
        
        if card_type == 'student' and not student:
            raise forms.ValidationError('Please select a student.')
        if card_type == 'teacher' and not teacher:
            raise forms.ValidationError('Please select a teacher.')
        
        # Check if card already exists
        if card_type == 'student' and student:
            if LibraryCard.objects.filter(student=student).exists():
                raise forms.ValidationError('Library card already exists for this student.')
        
        if card_type == 'teacher' and teacher:
            if LibraryCard.objects.filter(teacher=teacher).exists():
                raise forms.ValidationError('Library card already exists for this teacher.')
        
        return cleaned_data


class BookSearchForm(forms.Form):
    query = forms.CharField(max_length=200, required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Search by title, author, ISBN...', 'class': 'form-control'}
    ))
    category = forms.ModelChoiceField(
        queryset=BookCategory.objects.all(),
        required=False,
        empty_label="All Categories"
    )
    language = forms.ChoiceField(
        choices=[('', 'All Languages')] + list(Book.LANGUAGE_CHOICES),  # Fixed: converted tuple to list
        required=False
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(Book.STATUS_CHOICES),  # Fixed: converted tuple to list
        required=False
    )