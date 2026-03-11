from django import forms
from .models import (
    FeeCategory, FeeStructure, Concession, Invoice, InvoiceItem,
    Payment, ExpenseCategory, Expense, DueDate
)
from students.models import Student
from classes.models import Class
from decimal import Decimal

class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['academic_year', 'class_group', 'category', 'amount', 
                 'due_date', 'late_fee', 'discount', 'description', 
                 'is_installment', 'installment_number', 'is_active']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ConcessionForm(forms.ModelForm):
    class Meta:
        model = Concession
        fields = ['student', 'concession_type', 'percentage', 'amount', 
                 'reason', 'valid_from', 'valid_to', 'is_active']
        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date'}),
            'valid_to': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        
        if valid_from and valid_to and valid_from > valid_to:
            raise forms.ValidationError("Valid To date must be after Valid From date")
        
        return cleaned_data


class GenerateInvoiceForm(forms.Form):
    """Form to generate invoices for students"""
    academic_year = forms.ModelChoiceField(queryset=None, label="Academic Year")
    class_group = forms.ModelChoiceField(queryset=None, label="Class")
    due_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import AcademicYear
        self.fields['academic_year'].queryset = AcademicYear.objects.filter(is_current=True)
        self.fields['class_group'].queryset = Class.objects.filter(is_active=True)


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['student', 'academic_year', 'due_date', 'notes', 'terms']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'terms': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.filter(is_active=True)


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['fee_structure', 'description', 'quantity', 'unit_price', 'discount']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fee_structure'].required = False
        self.fields['fee_structure'].queryset = FeeStructure.objects.filter(is_active=True)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'invoice', 'amount', 'payment_method', 
                 'reference_number', 'bank_name', 'cheque_date', 'remarks']
        widgets = {
            'cheque_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.filter(is_active=True)
        self.fields['invoice'].queryset = Invoice.objects.exclude(status='paid')
        self.fields['invoice'].required = False


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'description', 'amount', 'expense_date', 
                 'payment_method', 'payment_reference', 'paid_to', 
                 'bill_number', 'bill_copy', 'remarks']
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }


class DueDateForm(forms.ModelForm):
    class Meta:
        model = DueDate
        fields = ['academic_year', 'title', 'description', 'due_date', 'is_active']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class FeeReportForm(forms.Form):
    """Form for fee reports"""
    REPORT_TYPES = (
        ('collection', 'Fee Collection Report'),
        ('pending', 'Pending Dues Report'),
        ('concession', 'Concession Report'),
        ('class_wise', 'Class Wise Collection'),
    )
    
    report_type = forms.ChoiceField(choices=REPORT_TYPES)
    academic_year = forms.ModelChoiceField(queryset=None)
    class_group = forms.ModelChoiceField(queryset=Class.objects.filter(is_active=True), required=False)
    from_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    to_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import AcademicYear
        self.fields['academic_year'].queryset = AcademicYear.objects.all()