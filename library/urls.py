from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.library_dashboard, name='library_dashboard'),
    
    # Book Management
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.book_add, name='book_add'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('books/<int:pk>/edit/', views.book_edit, name='book_edit'),
    path('books/<int:pk>/delete/', views.book_delete, name='book_delete'),
    
    # Issue/Return
    path('issues/', views.issue_list, name='issue_list'),
    path('issues/issue-book/', views.issue_book, name='issue_book'),
    path('issues/return-book/', views.return_book, name='return_book'),
    path('issues/<int:pk>/', views.issue_detail, name='issue_detail'),
    path('issues/<int:pk>/renew/', views.renew_book, name='renew_book'),
    
    # Reservations
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/create/', views.create_reservation, name='create_reservation'),
    path('reservations/<int:pk>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    
    # Requests
    path('requests/', views.request_list, name='request_list'),
    path('requests/create/', views.create_request, name='create_request'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    
    # Authors
    path('authors/', views.author_list, name='author_list'),
    path('authors/add/', views.author_add, name='author_add'),
    
    # Library Cards
    path('cards/', views.card_list, name='card_list'),
    path('cards/create/', views.card_create, name='card_create'),
    path('cards/<int:pk>/', views.card_detail, name='card_detail'),
    
    # Reports
    path('reports/', views.library_reports, name='library_reports'),
]