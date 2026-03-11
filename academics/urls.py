from django.urls import path
from . import views

urlpatterns = [
    # Exam URLs
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.exam_create, name='exam_create'),
    path('exams/<int:pk>/', views.exam_detail, name='exam_detail'),
    path('exams/<int:pk>/edit/', views.exam_edit, name='exam_edit'),
    path('exams/<int:pk>/delete/', views.exam_delete, name='exam_delete'),
    
    # Exam Subject URLs
    path('exams/<int:exam_id>/subjects/add/', views.exam_subject_add, name='exam_subject_add'),
    path('exam-subjects/<int:pk>/edit/', views.exam_subject_edit, name='exam_subject_edit'),
    path('exam-subjects/<int:pk>/delete/', views.exam_subject_delete, name='exam_subject_delete'),
    
    # Marks Entry URLs
    path('marks/<int:exam_subject_id>/', views.marks_entry, name='marks_entry'),
    path('marks/<int:exam_subject_id>/student/<int:student_id>/', views.marks_entry_single, name='marks_entry_single'),
    
    # Result URLs
    path('exams/<int:exam_id>/generate-results/', views.generate_results, name='generate_results'),
    path('exams/<int:exam_id>/results/', views.exam_results, name='exam_results'),
    path('exams/<int:exam_id>/publish-results/', views.publish_results, name='publish_results'),
    path('results/<int:result_id>/', views.student_result_detail, name='student_result_detail'),
    
    # Grade System URLs
    path('grade-systems/', views.grade_system_list, name='grade_system_list'),
    path('grade-systems/add/', views.grade_system_create, name='grade_system_create'),
    path('grade-systems/<int:pk>/edit/', views.grade_system_edit, name='grade_system_edit'),
    
    # Report Card URLs
    path('report-cards/<int:result_id>/generate/', views.generate_report_card, name='generate_report_card'),
    path('report-cards/<int:pk>/download/', views.download_report_card, name='download_report_card'),
]