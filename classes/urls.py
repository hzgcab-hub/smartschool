from django.urls import path
from . import views

urlpatterns = [
    # Class URLs
    path('', views.class_list, name='class_list'),
    path('add/', views.class_create, name='class_create'),
    path('<int:pk>/', views.class_detail, name='class_detail'),
    path('<int:pk>/edit/', views.class_edit, name='class_edit'),
    path('<int:pk>/delete/', views.class_delete, name='class_delete'),
    
    # Section URLs
    path('sections/', views.section_list, name='section_list'),
    path('sections/add/', views.section_create, name='section_create'),
    path('sections/<int:pk>/edit/', views.section_edit, name='section_edit'),
    
    # Subject URLs
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    
    # Timetable URLs
    path('timetable/', views.timetable_view, name='timetable_select'),
    path('timetable/<int:class_id>/', views.timetable_view, name='timetable_view'),
    path('timetable/add/', views.timetable_add, name='timetable_add'),
    
    # Homework URLs
    path('homework/', views.homework_list, name='homework_list'),
    path('homework/add/', views.homework_create, name='homework_create'),
    path('homework/<int:pk>/', views.homework_detail, name='homework_detail'),
    path('homework/<int:pk>/submit/', views.homework_submit, name='homework_submit'),
]