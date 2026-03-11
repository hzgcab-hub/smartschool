from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Student, StudentAttendance, StudentDocument
from .forms import StudentRegistrationForm, StudentAttendanceForm, StudentDocumentForm

@login_required
def student_list(request):
    """View all students with search and filter"""
    students = Student.objects.filter(is_active=True)
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        students = students.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(admission_number__icontains=query) |
            Q(current_class__icontains=query)
        )
    
    # Filter by class
    class_filter = request.GET.get('class')
    if class_filter:
        students = students.filter(current_class=class_filter)
    
    # Pagination
    paginator = Paginator(students, 20)  # Show 20 students per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique classes for filter dropdown
    classes = Student.objects.values_list('current_class', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'classes': classes,
        'query': query,
        'class_filter': class_filter,
    }
    return render(request, 'students/student_list.html', context)

@login_required
def student_detail(request, pk):
    """View single student details"""
    student = get_object_or_404(Student, pk=pk)
    attendance = student.attendance.all()[:30]  # Last 30 days attendance
    documents = student.documents.all()
    
    context = {
        'student': student,
        'attendance': attendance,
        'documents': documents,
    }
    return render(request, 'students/student_detail.html', context)

@login_required
def student_create(request):
    """Create new student"""
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student {student.get_full_name()} created successfully!')
            return redirect('student_detail', pk=student.pk)
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Add New Student'})

@login_required
def student_edit(request, pk):
    """Edit student details"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('student_detail', pk=student.pk)
    else:
        # Initialize form with student data
        initial_data = {
            'username': student.user.username,
            'first_name': student.user.first_name,
            'last_name': student.user.last_name,
            'email': student.user.email,
        }
        form = StudentRegistrationForm(instance=student, initial=initial_data)
    
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Edit Student'})

@login_required
def student_delete(request, pk):
    """Soft delete student (set inactive)"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        student.is_active = False
        student.user.is_active = False
        student.user.save()
        student.save()
        messages.success(request, 'Student deactivated successfully!')
        return redirect('student_list')
    
    return render(request, 'students/student_confirm_delete.html', {'student': student})

@login_required
def mark_attendance(request):
    """Mark attendance for students"""
    if request.method == 'POST':
        # Process attendance form
        date = request.POST.get('date')
        class_name = request.POST.get('class_name')
        
        for key, value in request.POST.items():
            if key.startswith('status_'):
                student_id = key.replace('status_', '')
                try:
                    student = Student.objects.get(id=student_id)
                    attendance, created = StudentAttendance.objects.update_or_create(
                        student=student,
                        date=date,
                        defaults={
                            'status': value,
                            'marked_by': request.user
                        }
                    )
                except Student.DoesNotExist:
                    continue
        
        messages.success(request, f'Attendance marked for {date}')
        return redirect('attendance_report')
    
    # GET request - show attendance form
    class_name = request.GET.get('class')
    date = request.GET.get('date')
    
    if class_name and date:
        students = Student.objects.filter(current_class=class_name, is_active=True)
        # Get existing attendance for this date
        attendance_records = StudentAttendance.objects.filter(
            student__in=students,
            date=date
        ).select_related('student')
        
        attendance_dict = {a.student_id: a for a in attendance_records}
        
        context = {
            'students': students,
            'class_name': class_name,
            'date': date,
            'attendance_dict': attendance_dict,
        }
        return render(request, 'students/mark_attendance.html', context)
    
    # Show class selection form
    classes = Student.objects.values_list('current_class', flat=True).distinct()
    return render(request, 'students/select_attendance_class.html', {'classes': classes})

@login_required
def attendance_report(request):
    """View attendance report"""
    class_name = request.GET.get('class')
    month = request.GET.get('month')
    
    attendance_data = None
    
    if class_name and month:
        year, month_num = map(int, month.split('-'))
        
        students = Student.objects.filter(current_class=class_name, is_active=True)
        attendance_data = []
        
        for student in students:
            monthly_attendance = student.attendance.filter(
                date__year=year,
                date__month=month_num
            )
            
            total_days = monthly_attendance.count()
            present_days = monthly_attendance.filter(status='present').count()
            absent_days = monthly_attendance.filter(status='absent').count()
            late_days = monthly_attendance.filter(status='late').count()
            
            attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
            
            attendance_data.append({
                'student': student,
                'total': total_days,
                'present': present_days,
                'absent': absent_days,
                'late': late_days,
                'percentage': round(attendance_percentage, 2)
            })
    
    classes = Student.objects.values_list('current_class', flat=True).distinct()
    
    context = {
        'classes': classes,
        'attendance_data': attendance_data,
        'selected_class': class_name,
        'selected_month': month,
    }
    return render(request, 'students/attendance_report.html', context)
