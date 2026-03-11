from django.contrib import admin
from .models import (
    FeeCategory, FeeStructure, Concession, Invoice, InvoiceItem,
    Payment, ExpenseCategory, Expense, FeeReminder, DueDate
)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_number', 'payment_date', 'receipt_number')

@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_mandatory', 'is_recurring', 'recurrence_period')
    list_filter = ('is_mandatory', 'is_recurring')
    search_fields = ('name',)

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('class_group', 'category', 'amount', 'due_date', 'is_active')
    list_filter = ('academic_year', 'class_group', 'category', 'is_active')
    search_fields = ('class_group__name', 'category__name')
    date_hierarchy = 'due_date'

@admin.register(Concession)
class ConcessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'concession_type', 'percentage', 'amount', 'valid_from', 'valid_to', 'is_active')
    list_filter = ('concession_type', 'is_active')
    search_fields = ('student__user__first_name', 'student__admission_number')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'student', 'issue_date', 'due_date', 'total', 'paid_amount', 'due_amount', 'status')
    list_filter = ('status', 'academic_year')
    search_fields = ('invoice_number', 'student__user__first_name', 'student__admission_number')
    readonly_fields = ('invoice_number', 'subtotal', 'total', 'paid_amount', 'due_amount')
    date_hierarchy = 'issue_date'
    inlines = [InvoiceItemInline, PaymentInline]
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'student', 'academic_year', 'status')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'discount', 'late_fee', 'total', 'paid_amount', 'due_amount')
        }),
        ('Additional Info', {
            'fields': ('notes', 'terms', 'created_by')
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'student', 'amount', 'payment_method', 'status', 'payment_date')
    list_filter = ('status', 'payment_method')
    search_fields = ('receipt_number', 'payment_number', 'student__user__first_name')
    readonly_fields = ('payment_number', 'receipt_number', 'transaction_id')
    date_hierarchy = 'payment_date'

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_number', 'description', 'category', 'amount', 'expense_date', 'status')
    list_filter = ('category', 'status', 'payment_method')
    search_fields = ('expense_number', 'description', 'paid_to')
    date_hierarchy = 'expense_date'
    readonly_fields = ('expense_number',)

@admin.register(FeeReminder)
class FeeReminderAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'reminder_type', 'sent_date', 'is_successful')
    list_filter = ('reminder_type', 'is_successful')

@admin.register(DueDate)
class DueDateAdmin(admin.ModelAdmin):
    list_display = ('title', 'due_date', 'academic_year', 'is_active')
    list_filter = ('academic_year', 'is_active')
    date_hierarchy = 'due_date'