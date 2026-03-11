from django.contrib import admin
from .models import (
    BookCategory, BookPublisher, BookAuthor, Book,
    BookIssue, BookReservation, BookRequest,
    LibrarySetting, LibraryCard
)

class BookAuthorInline(admin.TabularInline):
    model = Book.authors.through
    extra = 1

@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(BookPublisher)
class BookPublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')
    search_fields = ('name',)

@admin.register(BookAuthor)
class BookAuthorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'birth_date', 'death_date')
    search_fields = ('first_name', 'last_name')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'isbn', 'category', 'total_copies', 'available_copies', 'status')
    list_filter = ('category', 'language', 'status', 'publication_year')
    search_fields = ('title', 'isbn', 'accession_number', 'authors__first_name', 'authors__last_name')
    list_editable = ('status',)
    filter_horizontal = ('authors',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'isbn', 'authors', 'category', 'publisher')
        }),
        ('Publication Details', {
            'fields': ('publication_year', 'edition', 'volume', 'pages', 'language')
        }),
        ('Library Details', {
            'fields': ('accession_number', 'shelf_location', 'rack_number')
        }),
        ('Copies', {
            'fields': ('total_copies', 'available_copies')
        }),
        ('Additional Info', {
            'fields': ('description', 'keywords', 'cover_image')
        }),
        ('Pricing', {
            'fields': ('price', 'late_fee_per_day')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
    )
    
    readonly_fields = ('accession_number',)

@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower_name', 'issue_date', 'due_date', 'return_date', 'status', 'fine_amount')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('book__title', 'book__isbn', 'student__user__first_name', 'teacher__user__first_name')
    date_hierarchy = 'issue_date'
    readonly_fields = ('fine_amount',)
    
    fieldsets = (
        ('Book Information', {
            'fields': ('book',)
        }),
        ('Borrower Information', {
            'fields': ('student', 'teacher')
        }),
        ('Issue Details', {
            'fields': ('issue_date', 'due_date', 'return_date')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Fine', {
            'fields': ('fine_amount', 'fine_paid', 'fine_paid_date')
        }),
        ('Tracking', {
            'fields': ('issued_by', 'received_by', 'remarks')
        }),
    )

@admin.register(BookReservation)
class BookReservationAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower_name', 'reservation_date', 'expiry_date', 'status')
    list_filter = ('status', 'reservation_date')
    search_fields = ('book__title', 'student__user__first_name', 'teacher__user__first_name')

@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'user', 'priority', 'status', 'created_at')
    list_filter = ('priority', 'status', 'created_at')
    search_fields = ('title', 'author', 'user__username')
    date_hierarchy = 'created_at'
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        queryset.update(status='approved', approved_by=request.user, approved_date=date.today())
    approve_requests.short_description = "Approve selected requests"
    
    def reject_requests(self, request, queryset):
        queryset.update(status='rejected', approved_by=request.user, approved_date=date.today())
    reject_requests.short_description = "Reject selected requests"

@admin.register(LibraryCard)
class LibraryCardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'owner_name', 'owner_type', 'issued_date', 'expiry_date', 'status')
    list_filter = ('status', 'issued_date', 'expiry_date')
    search_fields = ('card_number', 'student__user__first_name', 'teacher__user__first_name')
    readonly_fields = ('card_number',)

@admin.register(LibrarySetting)
class LibrarySettingAdmin(admin.ModelAdmin):
    list_display = ('late_fee_per_day', 'max_books_per_student', 'max_books_per_teacher')
    
    def has_add_permission(self, request):
        # Only allow one settings object
        return not LibrarySetting.objects.exists()
