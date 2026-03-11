from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.models import User
from students.models import Student
from teachers.models import Teacher, TeacherSubject
from classes.models import Class, Section, Homework  # Fixed: Homework is here
from academics.models import Exam  # Removed Homework from here
from finance.models import Invoice, Payment
from library.models import BookIssue
from notices.models import Notice
from django.db.models import Count, Sum
from datetime import date, timedelta

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Role-based redirect
            if user.role == 'super_admin' or user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'teacher':
                return redirect('teacher_dashboard')
            elif user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'parent':
                return redirect('parent_dashboard')
            elif user.role == 'accountant':
                return redirect('finance_dashboard')
            elif user.role == 'librarian':
                return redirect('library_dashboard')
            else:
                return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def admin_dashboard(request):
    """Super Admin / Admin Dashboard"""
    # Statistics
    total_students = Student.objects.filter(is_active=True).count()
    total_teachers = Teacher.objects.filter(is_active=True).count()
    total_classes = Class.objects.filter(is_active=True).count()
    
    # Recent activities
    recent_students = Student.objects.filter(is_active=True).order_by('-created_at')[:5]
    recent_teachers = Teacher.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Financial summary
    today = date.today()
    month_start = today.replace(day=1)
    
    monthly_collections = Payment.objects.filter(
        payment_date__date__gte=month_start,
        status='completed'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'recent_students': recent_students,
        'recent_teachers': recent_teachers,
        'monthly_collections': monthly_collections,
    }
    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    """Teacher Dashboard"""
    try:
        teacher = request.user.teacher_profile
        
        # My classes
        my_classes = Class.objects.filter(class_teacher=teacher)[:5]
        
        # My subjects
        my_subjects = TeacherSubject.objects.filter(teacher=teacher)[:5]
        
        # Recent homework
        recent_homework = Homework.objects.filter(teacher=teacher).order_by('-created_at')[:5]
        
        context = {
            'teacher': teacher,
            'my_classes': my_classes,
            'my_subjects': my_subjects,
            'recent_homework': recent_homework,
        }
        return render(request, 'dashboards/teacher_dashboard.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found')
        return redirect('login')

@login_required
def student_dashboard(request):
    """Student Dashboard"""
    try:
        student = request.user.student_profile
        
        # Recent attendance
        recent_attendance = student.attendance.all().order_by('-date')[:10]
        
        # Upcoming exams
        upcoming_exams = Exam.objects.filter(
            class_group__name=student.current_class,
            start_date__gte=date.today()
        ).order_by('start_date')[:5]
        
        # Recent homework
        recent_homework = Homework.objects.filter(
            class_group__name=student.current_class,
            section__name=student.section
        ).order_by('-due_date')[:5]
        
        # Recent results
        recent_results = student.exam_results.filter(is_published=True).order_by('-exam__result_date')[:5]
        
        # Fee status
        pending_fees = Invoice.objects.filter(
            student=student,
            status__in=['pending', 'overdue']
        ).aggregate(Sum('due_amount'))['due_amount__sum'] or 0
        
        # Library books
        issued_books = BookIssue.objects.filter(student=student, status='issued').count()
        
        # Notices
        recent_notices = Notice.objects.filter(
            status='published',
            audience_type__in=['all', 'students']
        ).order_by('-publish_date')[:3]
        
        context = {
            'student': student,
            'recent_attendance': recent_attendance,
            'upcoming_exams': upcoming_exams,
            'recent_homework': recent_homework,
            'recent_results': recent_results,
            'pending_fees': pending_fees,
            'issued_books': issued_books,
            'recent_notices': recent_notices,
        }
        return render(request, 'dashboards/student_dashboard.html', context)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found')
        return redirect('login')

@login_required
def parent_dashboard(request):
    """Parent Dashboard"""
    # Get parent's children (students) - match by phone number
    phone = request.user.phone_number
    children = Student.objects.filter(
        father_phone=phone,
        is_active=True
    ) | Student.objects.filter(
        mother_phone=phone,
        is_active=True
    )
    
    context = {
        'children': children,
    }
    return render(request, 'dashboards/parent_dashboard.html', context)