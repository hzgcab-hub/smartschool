from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import User, AcademicYear
from students.models import Student
from classes.models import Class
from decimal import Decimal
import datetime

class FeeCategory(models.Model):
    """Types of fees"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=True)
    is_recurring = models.BooleanField(default=False, help_text="Whether this fee recurs every month/term")
    recurrence_period = models.CharField(max_length=20, choices=(
        ('one_time', 'One Time'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half Yearly'),
        ('yearly', 'Yearly'),
    ), default='one_time')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Fee Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class FeeStructure(models.Model):
    """Fee structure for classes"""
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='fee_structures')
    class_group = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='fee_structures')
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name='fee_structures')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    due_date = models.DateField()
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Late fee if paid after due date")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Discount amount")
    description = models.TextField(blank=True)
    is_installment = models.BooleanField(default=False)
    installment_number = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['academic_year', 'class_group', 'category', 'installment_number']
        ordering = ['due_date']
    
    def __str__(self):
        return f"{self.class_group.name} - {self.category.name} - ₹{self.amount}"
    
    @property
    def net_amount(self):
        """Amount after discount"""
        return self.amount - self.discount


class Concession(models.Model):
    """Fee concessions for students"""
    CONCESSION_TYPES = (
        ('scholarship', 'Scholarship'),
        ('sibling', 'Sibling Concession'),
        ('staff', 'Staff Concession'),
        ('merit', 'Merit Based'),
        ('need', 'Need Based'),
        ('other', 'Other'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='concessions')
    concession_type = models.CharField(max_length=20, choices=CONCESSION_TYPES)
    percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Fixed amount if not percentage")
    reason = models.TextField()
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_concessions')
    valid_from = models.DateField()
    valid_to = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student} - {self.get_concession_type_display()}"


class Invoice(models.Model):
    """Student fee invoice"""
    INVOICE_STATUS = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )
    
    invoice_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='invoices')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='invoices')
    
    # Invoice details
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='draft')
    
    # Totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Notes
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.student}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number: INV/YYYY/XXXX
            year = datetime.date.today().year
            last_invoice = Invoice.objects.filter(invoice_number__startswith=f"INV/{year}/").order_by('id').last()
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1001
            self.invoice_number = f"INV/{year}/{new_number:04d}"
        
        self.due_amount = self.total - self.paid_amount
        
        # Update status based on payment
        if self.paid_amount >= self.total:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partial'
        elif datetime.date.today() > self.due_date and self.paid_amount == 0:
            self.status = 'overdue'
        
        super().save(*args, **kwargs)


class InvoiceItem(models.Model):
    """Individual items in an invoice"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total = (self.unit_price * self.quantity) - self.discount
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.description} - {self.total}"


class Payment(models.Model):
    """Student payments"""
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online Transfer'),
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('bank_draft', 'Bank Draft'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    )
    
    payment_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # For cheque/DD
    reference_number = models.CharField(max_length=100, blank=True, help_text="Cheque/DD/Transaction number")
    bank_name = models.CharField(max_length=100, blank=True)
    cheque_date = models.DateField(null=True, blank=True)
    
    # Receipt
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    receipt_date = models.DateField(auto_now_add=True)
    
    # Remarks
    remarks = models.TextField(blank=True)
    
    # Tracking
    collected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='collected_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.receipt_number} - {self.student} - ₹{self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.payment_number:
            # Generate payment number: PAY/YYYY/XXXX
            year = datetime.date.today().year
            last_payment = Payment.objects.filter(payment_number__startswith=f"PAY/{year}/").order_by('id').last()
            if last_payment:
                last_number = int(last_payment.payment_number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1001
            self.payment_number = f"PAY/{year}/{new_number:04d}"
        
        if not self.receipt_number and self.status == 'completed':
            # Generate receipt number: RCPT/YYYY/XXXX
            year = datetime.date.today().year
            last_receipt = Payment.objects.filter(receipt_number__startswith=f"RCPT/{year}/").order_by('id').last()
            if last_receipt:
                last_number = int(last_receipt.receipt_number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1001
            self.receipt_number = f"RCPT/{year}/{new_number:04d}"
        
        if not self.transaction_id:
            self.transaction_id = f"TXN{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{self.student.id}"
        
        super().save(*args, **kwargs)
        
        # Update invoice paid amount if payment is completed and linked to invoice
        if self.invoice and self.status == 'completed':
            invoice = self.invoice
            invoice.paid_amount += self.amount
            invoice.save()


class ExpenseCategory(models.Model):
    """Categories for expenses"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Expense(models.Model):
    """School expenses"""
    EXPENSE_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    )
    
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online Transfer'),
        ('card', 'Card'),
    )
    
    expense_number = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name='expenses')
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Date
    expense_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    
    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_reference = models.CharField(max_length=100, blank=True)
    paid_to = models.CharField(max_length=200)
    
    # Status
    status = models.CharField(max_length=20, choices=EXPENSE_STATUS, default='pending')
    
    # Receipt/Attachment
    bill_number = models.CharField(max_length=100, blank=True)
    bill_copy = models.FileField(upload_to='expenses/', blank=True, null=True)
    
    # Approval
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requested_expenses')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_expenses')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Remarks
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expense_date']
    
    def __str__(self):
        return f"{self.expense_number} - {self.description[:50]} - ₹{self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.expense_number:
            # Generate expense number: EXP/YYYY/XXXX
            year = datetime.date.today().year
            last_expense = Expense.objects.filter(expense_number__startswith=f"EXP/{year}/").order_by('id').last()
            if last_expense:
                last_number = int(last_expense.expense_number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1001
            self.expense_number = f"EXP/{year}/{new_number:04d}"
        
        super().save(*args, **kwargs)


class FeeReminder(models.Model):
    """Fee payment reminders"""
    REMINDER_TYPE = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Both'),
    )
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=10, choices=REMINDER_TYPE)
    sent_date = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    response = models.TextField(blank=True)
    is_successful = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Reminder for {self.invoice} - {self.sent_date}"


class DueDate(models.Model):
    """Important due dates for fee payments"""
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='due_dates')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['due_date']
    
    def __str__(self):
        return f"{self.title} - {self.due_date}"
