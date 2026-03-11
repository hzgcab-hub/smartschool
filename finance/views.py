from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    FeeCategory, FeeStructure, Concession, Invoice, InvoiceItem,
    Payment, ExpenseCategory, Expense, DueDate
)
from .forms import (
    FeeStructureForm, ConcessionForm, GenerateInvoiceForm,
    InvoiceForm, InvoiceItemForm, PaymentForm, ExpenseForm,
    DueDateForm, FeeReportForm
)
from students.models import Student
from classes.models import Class
from core.models import AcademicYear

# ========== Dashboard ==========
@login_required
def finance_dashboard(request):
    """Finance dashboard with summary"""
    # Today's collections
    today = timezone.now().date()
    today_collections = Payment.objects.filter(
        payment_date__date=today,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Monthly collections
    month_start = today.replace(day=1)
    monthly_collections = Payment.objects.filter(
        payment_date__date__gte=month_start,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Pending dues
    pending_invoices = Invoice.objects.exclude(status='paid').aggregate(
        total=Sum('due_amount')
    )['total'] or 0
    
    # Total expenses this month
    monthly_expenses = Expense.objects.filter(
        expense_date__gte=month_start,
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent payments
    recent_payments = Payment.objects.filter(status='completed').order_by('-payment_date')[:10]
    
    # Upcoming due dates
    upcoming_dates = DueDate.objects.filter(
        due_date__gte=today,
        is_active=True
    ).order_by('due_date')[:5]
    
    # Statistics for cards
    total_invoices = Invoice.objects.count()
    paid_invoices = Invoice.objects.filter(status='paid').count()
    pending_invoices_count = Invoice.objects.exclude(status='paid').count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'today_collections': today_collections,
        'monthly_collections': monthly_collections,
        'pending_invoices': pending_invoices,
        'monthly_expenses': monthly_expenses,
        'recent_payments': recent_payments,
        'upcoming_dates': upcoming_dates,
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'pending_invoices_count': pending_invoices_count,
        'total_revenue': total_revenue,
    }
    return render(request, 'finance/dashboard.html', context)

# ========== Fee Structure Views ==========
@login_required
def fee_structure_list(request):
    """List all fee structures"""
    fee_structures = FeeStructure.objects.filter(is_active=True).select_related('class_group', 'category')
    
    # Filter by class
    class_id = request.GET.get('class')
    if class_id:
        fee_structures = fee_structures.filter(class_group_id=class_id)
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        fee_structures = fee_structures.filter(category_id=category_id)
    
    # Filter by academic year
    year_id = request.GET.get('academic_year')
    if year_id:
        fee_structures = fee_structures.filter(academic_year_id=year_id)
    
    paginator = Paginator(fee_structures, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    classes = Class.objects.filter(is_active=True)
    categories = FeeCategory.objects.all()
    academic_years = AcademicYear.objects.all()
    
    context = {
        'page_obj': page_obj,
        'classes': classes,
        'categories': categories,
        'academic_years': academic_years,
        'class_id': class_id,
        'category_id': category_id,
        'year_id': year_id,
    }
    return render(request, 'finance/fee_structure_list.html', context)

@login_required
def fee_structure_add(request):
    """Add new fee structure"""
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            fee_structure = form.save()
            messages.success(request, 'Fee structure added successfully!')
            return redirect('fee_structure_list')
    else:
        form = FeeStructureForm()
    
    return render(request, 'finance/fee_structure_form.html', {
        'form': form,
        'title': 'Add Fee Structure'
    })

@login_required
def fee_structure_edit(request, pk):
    """Edit fee structure"""
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    
    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fee_structure)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee structure updated successfully!')
            return redirect('fee_structure_list')
    else:
        form = FeeStructureForm(instance=fee_structure)
    
    return render(request, 'finance/fee_structure_form.html', {
        'form': form,
        'title': 'Edit Fee Structure'
    })

@login_required
def fee_structure_delete(request, pk):
    """Delete fee structure"""
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    
    if request.method == 'POST':
        fee_structure.is_active = False
        fee_structure.save()
        messages.success(request, 'Fee structure deleted successfully!')
        return redirect('fee_structure_list')
    
    return render(request, 'finance/fee_structure_confirm_delete.html', {'fee_structure': fee_structure})

# ========== Invoice Views ==========
@login_required
def invoice_list(request):
    """List all invoices"""
    invoices = Invoice.objects.all().select_related('student', 'academic_year')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        invoices = invoices.filter(status=status)
    
    # Filter by student
    student_id = request.GET.get('student')
    if student_id:
        invoices = invoices.filter(student_id=student_id)
    
    # Search
    query = request.GET.get('q')
    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query) |
            Q(student__user__first_name__icontains=query) |
            Q(student__user__last_name__icontains=query) |
            Q(student__admission_number__icontains=query)
        )
    
    # Calculate stats for cards
    total_invoices = invoices.count()
    paid_invoices = invoices.filter(status='paid').count()
    unpaid_invoices = invoices.exclude(status='paid').count()
    total_amount = invoices.aggregate(Sum('total'))['total__sum'] or 0
    
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
        'query': query,
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'unpaid_invoices': unpaid_invoices,
        'total_amount': total_amount,
    }
    return render(request, 'finance/invoice_list.html', context)

@login_required
def invoice_detail(request, pk):
    """View invoice details"""
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()
    payments = invoice.payments.all()
    
    context = {
        'invoice': invoice,
        'items': items,
        'payments': payments,
    }
    return render(request, 'finance/invoice_detail.html', context)

@login_required
def invoice_create(request):
    """Create new invoice"""
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.save()
            messages.success(request, 'Invoice created successfully! Add items now.')
            return redirect('invoice_add_item', pk=invoice.pk)
    else:
        form = InvoiceForm()
    
    return render(request, 'finance/invoice_form.html', {
        'form': form,
        'title': 'Create Invoice'
    })

@login_required
def invoice_add_item(request, pk):
    """Add items to invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        form = InvoiceItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.invoice = invoice
            item.save()
            
            # Update invoice totals
            items = invoice.items.all()
            invoice.subtotal = sum(item.total for item in items)
            invoice.total = invoice.subtotal - invoice.discount + invoice.late_fee
            invoice.save()
            
            messages.success(request, 'Item added to invoice!')
            return redirect('invoice_add_item', pk=invoice.pk)
    else:
        form = InvoiceItemForm()
    
    items = invoice.items.all()
    
    context = {
        'invoice': invoice,
        'form': form,
        'items': items,
    }
    return render(request, 'finance/invoice_add_item.html', context)

@login_required
def invoice_generate_bulk(request):
    """Generate invoices in bulk for a class"""
    if request.method == 'POST':
        form = GenerateInvoiceForm(request.POST)
        if form.is_valid():
            academic_year = form.cleaned_data['academic_year']
            class_group = form.cleaned_data['class_group']
            due_date = form.cleaned_data['due_date']
            
            # Get all students in this class
            students = Student.objects.filter(current_class=class_group.name, is_active=True)
            
            # Get fee structures for this class
            fee_structures = FeeStructure.objects.filter(
                class_group=class_group,
                academic_year=academic_year,
                is_active=True
            )
            
            if not fee_structures.exists():
                messages.error(request, 'No fee structures found for this class!')
                return redirect('invoice_list')
            
            invoices_created = 0
            
            with transaction.atomic():
                for student in students:
                    # Check if invoice already exists
                    if Invoice.objects.filter(
                        student=student,
                        academic_year=academic_year
                    ).exists():
                        continue
                    
                    # Create invoice
                    invoice = Invoice.objects.create(
                        student=student,
                        academic_year=academic_year,
                        due_date=due_date,
                        status='sent',
                        created_by=request.user
                    )
                    
                    # Add fee items
                    for fee in fee_structures:
                        InvoiceItem.objects.create(
                            invoice=invoice,
                            fee_structure=fee,
                            description=f"{fee.category.name} - {fee.class_group.name}",
                            quantity=1,
                            unit_price=fee.net_amount,
                            total=fee.net_amount
                        )
                    
                    # Update invoice totals
                    items = invoice.items.all()
                    invoice.subtotal = sum(item.total for item in items)
                    invoice.total = invoice.subtotal
                    invoice.save()
                    
                    invoices_created += 1
            
            messages.success(request, f'{invoices_created} invoices generated successfully!')
            return redirect('invoice_list')
    else:
        form = GenerateInvoiceForm()
    
    return render(request, 'finance/invoice_generate_bulk.html', {'form': form})

# ========== Payment Views ==========
@login_required
def payment_list(request):
    """List all payments"""
    payments = Payment.objects.all().select_related('student', 'collected_by')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        payments = payments.filter(status=status)
    
    # Filter by payment method
    method = request.GET.get('method')
    if method:
        payments = payments.filter(payment_method=method)
    
    # Search
    query = request.GET.get('q')
    if query:
        payments = payments.filter(
            Q(receipt_number__icontains=query) |
            Q(payment_number__icontains=query) |
            Q(student__user__first_name__icontains=query) |
            Q(student__admission_number__icontains=query)
        )
    
    # Calculate stats for cards
    total_transactions = payments.count()
    completed_count = payments.filter(status='completed').count()
    pending_count = payments.filter(status='pending').count()
    total_amount = payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
        'method': method,
        'query': query,
        'total_transactions': total_transactions,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'total_amount': total_amount,
    }
    return render(request, 'finance/payment_list.html', context)

@login_required
def payment_create(request):
    """Record new payment"""
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.collected_by = request.user
            payment.status = 'completed'
            payment.save()
            messages.success(request, f'Payment recorded! Receipt: {payment.receipt_number}')
            return redirect('payment_detail', pk=payment.pk)
    else:
        # Pre-fill student and invoice if provided
        student_id = request.GET.get('student')
        invoice_id = request.GET.get('invoice')
        initial = {}
        if student_id:
            initial['student'] = student_id
        if invoice_id:
            initial['invoice'] = invoice_id
        
        form = PaymentForm(initial=initial)
    
    return render(request, 'finance/payment_form.html', {
        'form': form,
        'title': 'Record Payment'
    })

@login_required
def payment_detail(request, pk):
    """View payment details"""
    payment = get_object_or_404(Payment, pk=pk)
    
    context = {
        'payment': payment,
    }
    return render(request, 'finance/payment_detail.html', context)

@login_required
def payment_receipt(request, pk):
    """View payment receipt (printable)"""
    payment = get_object_or_404(Payment, pk=pk)
    
    return render(request, 'finance/payment_receipt.html', {'payment': payment})

# ========== Expense Views ==========
@login_required
def expense_list(request):
    """List all expenses"""
    expenses = Expense.objects.all().select_related('category', 'requested_by')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        expenses = expenses.filter(status=status)
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        expenses = expenses.filter(category_id=category_id)
    
    # Search
    query = request.GET.get('q')
    if query:
        expenses = expenses.filter(
            Q(expense_number__icontains=query) |
            Q(description__icontains=query) |
            Q(paid_to__icontains=query)
        )
    
    # Calculate stats
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    pending_expenses = expenses.filter(status='pending').count()
    approved_expenses = expenses.filter(status='approved').count()
    paid_expenses = expenses.filter(status='paid').count()
    
    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = ExpenseCategory.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'status': status,
        'category_id': category_id,
        'query': query,
        'total_expenses': total_expenses,
        'pending_expenses': pending_expenses,
        'approved_expenses': approved_expenses,
        'paid_expenses': paid_expenses,
    }
    return render(request, 'finance/expense_list.html', context)

@login_required
def expense_create(request):
    """Create new expense request"""
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.requested_by = request.user
            expense.status = 'pending'
            expense.save()
            messages.success(request, 'Expense request submitted successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    
    return render(request, 'finance/expense_form.html', {
        'form': form,
        'title': 'Add Expense'
    })

@login_required
def expense_detail(request, pk):
    """View expense details"""
    expense = get_object_or_404(Expense, pk=pk)
    
    context = {
        'expense': expense,
    }
    return render(request, 'finance/expense_detail.html', context)

@login_required
def expense_approve(request, pk):
    """Approve or reject expense"""
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            expense.status = 'approved'
            messages.success(request, 'Expense approved!')
        elif action == 'reject':
            expense.status = 'rejected'
            messages.success(request, 'Expense rejected!')
        elif action == 'pay':
            expense.status = 'paid'
            expense.payment_date = timezone.now().date()
            messages.success(request, 'Expense marked as paid!')
        
        expense.approved_by = request.user
        expense.approved_at = timezone.now()
        expense.save()
        
        return redirect('expense_detail', pk=expense.pk)
    
    return render(request, 'finance/expense_approve.html', {'expense': expense})

# ========== Report Views ==========
@login_required
def fee_report(request):
    """Generate fee reports"""
    report_data = None
    
    if request.method == 'POST':
        form = FeeReportForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data['report_type']
            academic_year = form.cleaned_data['academic_year']
            class_group = form.cleaned_data['class_group']
            from_date = form.cleaned_data['from_date']
            to_date = form.cleaned_data['to_date']
            
            if report_type == 'collection':
                # Fee collection report
                payments = Payment.objects.filter(
                    payment_date__date__gte=from_date,
                    payment_date__date__lte=to_date,
                    status='completed'
                )
                
                if class_group:
                    payments = payments.filter(student__current_class=class_group.name)
                
                total_amount = payments.aggregate(Sum('amount'))['amount__sum'] or 0
                total_count = payments.count()
                
                report_data = {
                    'type': 'Fee Collection Report',
                    'total_amount': total_amount,
                    'total_count': total_count,
                    'payments': payments[:100],
                }
                
            elif report_type == 'pending':
                # Pending dues report
                invoices = Invoice.objects.exclude(status='paid')
                
                if class_group:
                    invoices = invoices.filter(student__current_class=class_group.name)
                
                total_pending = invoices.aggregate(Sum('due_amount'))['due_amount__sum'] or 0
                
                report_data = {
                    'type': 'Pending Dues Report',
                    'total_pending': total_pending,
                    'invoice_count': invoices.count(),
                    'invoices': invoices[:100],
                }
            
            elif report_type == 'concession':
                # Concession report
                concessions = Concession.objects.filter(
                    valid_from__lte=to_date,
                    valid_to__gte=from_date,
                    is_active=True
                )
                
                if class_group:
                    concessions = concessions.filter(student__current_class=class_group.name)
                
                total_concession = concessions.aggregate(Sum('amount'))['amount__sum'] or 0
                
                report_data = {
                    'type': 'Concession Report',
                    'total_concession': total_concession,
                    'concession_count': concessions.count(),
                    'concessions': concessions[:100],
                }
            
            elif report_type == 'class_wise':
                # Class wise collection
                classes = Class.objects.filter(is_active=True)
                class_data = []
                
                for cls in classes:
                    cls_payments = Payment.objects.filter(
                        student__current_class=cls.name,
                        payment_date__date__gte=from_date,
                        payment_date__date__lte=to_date,
                        status='completed'
                    )
                    
                    total = cls_payments.aggregate(Sum('amount'))['amount__sum'] or 0
                    count = cls_payments.count()
                    
                    if total > 0:
                        class_data.append({
                            'class': cls,
                            'total': total,
                            'count': count,
                        })
                
                report_data = {
                    'type': 'Class Wise Collection Report',
                    'class_data': class_data,
                    'grand_total': sum(item['total'] for item in class_data),
                }
    
    else:
        form = FeeReportForm()
    
    context = {
        'form': form,
        'report_data': report_data,
    }
    return render(request, 'finance/fee_report.html', context)