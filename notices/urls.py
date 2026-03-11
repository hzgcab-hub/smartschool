from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.notice_dashboard, name='notice_dashboard'),
    
    # Notice URLs
    path('notices/', views.notice_list, name='notice_list'),
    path('notices/create/', views.notice_create, name='notice_create'),
    path('notices/<int:pk>/', views.notice_detail, name='notice_detail'),
    path('notices/<int:pk>/edit/', views.notice_edit, name='notice_edit'),
    path('notices/<int:pk>/delete/', views.notice_delete, name='notice_delete'),
    path('notices/archive/', views.notice_archive, name='notice_archive'),
    
    # Event URLs
    path('events/', views.event_list, name='event_list'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    
    # Circular URLs
    path('circulars/', views.circular_list, name='circular_list'),
    path('circulars/<int:pk>/', views.circular_detail, name='circular_detail'),
    
    # Notification URLs
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/bulk/', views.bulk_notification, name='bulk_notification'),
    
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
]