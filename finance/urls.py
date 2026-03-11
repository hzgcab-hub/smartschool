from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.finance_dashboard, name='finance_dashboard'),
    
    # Fee Structure
    path('fee-structures/', views.fee_structure_list, name='fee_structure_list'),
    path('fee-structures/add/', views.fee_structure_add, name='fee_structure_add'),
    path('fee-structures/<int:pk>/edit/', views.fee_structure_edit, name='fee_structure_edit'),
    path('fee-structures/<int:pk>/delete/', views.fee_structure_delete, name='fee_structure_delete'),
    
    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/generate-bulk/', views.invoice_generate_bulk, name='invoice_generate_bulk'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/add-item/', views.invoice_add_item, name='invoice_add_item'),
    
    # Payments
    path('payments/', views.payment_list, name='payment_list'),  # This should be 'payment_list'
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:pk>/receipt/', views.payment_receipt, name='payment_receipt'),
    
    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/', views.expense_detail, name='expense_detail'),
    path('expenses/<int:pk>/approve/', views.expense_approve, name='expense_approve'),
    
    # Reports
    path('reports/fee/', views.fee_report, name='fee_report'),
]