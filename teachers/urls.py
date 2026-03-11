from django.urls import path
from . import views

urlpatterns = [
    path('', views.teacher_list, name='teacher_list'),
    path('add/', views.teacher_create, name='teacher_create'),
    path('<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),
    path('<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    path('attendance/mark/', views.mark_teacher_attendance, name='mark_teacher_attendance'),
    path('attendance/report/', views.teacher_attendance_report, name='teacher_attendance_report'),
    path('leaves/apply/', views.apply_leave, name='apply_leave'),
    path('leaves/my-leaves/', views.my_leaves, name='my_leaves'),
]