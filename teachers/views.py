from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from .models import Teacher, TeacherAttendance, TeacherLeave, TeacherQualification
from .forms import (
    TeacherRegistrationForm, TeacherEditForm, 
    TeacherAttendanceForm, TeacherLeaveForm,
    TeacherQualificationForm
)

@login_required
def teacher_list(request):
    """View all teachers with search and filter"""
    teachers = Teacher.objects.filter(is_active=True)
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        teachers = teachers.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(specialization__icontains=query) |
            Q(qualification__icontains=query)
        )
    
    # Filter by employment type
    emp_type = request.GET.get('employment_type')
    if emp_type:
        teachers = teachers.filter(employment_type=emp_type)
    
    # Filter by qualification level
    qual_level = request.GET.get('qualification')
    if qual_level:
        teachers = teachers.filter(qualification_level=qual_level)
    
    # Pagination
    paginator = Paginator(teachers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique values for filters
    employment_types = Teacher.objects.values_list('employment_type', flat=True).distinct()
    qualification_levels = Teacher.objects.values_list('qualification_level', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'employment_types': employment_types,
        'qualification_levels': qualification_levels,
        'query': query,
        'emp_type': emp_type,
        'qual_level': qual_level,
    }
    return render(request, 'teachers/teacher_list.html', context)

@login_required
def teacher_detail(request, pk):
    """View single teacher details"""
    teacher = get_object_or_404(Teacher, pk=pk)
    attendance = teacher.attendance.all()[:30]
    leaves = teacher.leaves.all()[:10]
    qualifications = teacher.qualifications.all()
    
    context = {
        'teacher': teacher,
        'attendance': attendance,
        'leaves': leaves,
        'qualifications': qualifications,
    }
    return render(request, 'teachers/teacher_detail.html', context)

@login_required
def teacher_create(request):
    """Create new teacher"""
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            teacher = form.save()
            messages.success(request, f'Teacher {teacher.get_full_name()} created successfully!')
            return redirect('teacher_detail', pk=teacher.pk)
    else:
        form = TeacherRegistrationForm()
    
    return render(request, 'teachers/teacher_form.html', {
        'form': form, 
        'title': 'Add New Teacher'
    })

@login_required
def teacher_edit(request, pk):
    """Edit teacher details"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        form = TeacherEditForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher updated successfully!')
            return redirect('teacher_detail', pk=teacher.pk)
    else:
        form = TeacherEditForm(instance=teacher)
    
    return render(request, 'teachers/teacher_form.html', {
        'form': form, 
        'title': 'Edit Teacher'
    })

@login_required
def teacher_delete(request, pk):
    """Soft delete teacher (set inactive)"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        teacher.is_active = False
        teacher.user.is_active = False
        teacher.user.save()
        teacher.save()
        messages.success(request, 'Teacher deactivated successfully!')
        return redirect('teacher_list')
    
    return render(request, 'teachers/teacher_confirm_delete.html', {'teacher': teacher})

@login_required
def mark_teacher_attendance(request):
    """Mark attendance for teachers"""
    if request.method == 'POST':
        date = request.POST.get('date')
        
        for key, value in request.POST.items():
            if key.startswith('status_'):
                teacher_id = key.replace('status_', '')
                check_in = request.POST.get(f'checkin_{teacher_id}')
                check_out = request.POST.get(f'checkout_{teacher_id}')
                
                try:
                    teacher = Teacher.objects.get(id=teacher_id)
                    
                    check_in_time = None
                    check_out_time = None
                    
                    if check_in:
                        check_in_time = datetime.strptime(check_in, '%H:%M').time()
                    if check_out:
                        check_out_time = datetime.strptime(check_out, '%H:%M').time()
                    
                    attendance, created = TeacherAttendance.objects.update_or_create(
                        teacher=teacher,
                        date=date,
                        defaults={
                            'status': value,
                            'check_in_time': check_in_time,
                            'check_out_time': check_out_time,
                            'marked_by': request.user
                        }
                    )
                except Teacher.DoesNotExist:
                    continue
        
        messages.success(request, f'Teacher attendance marked for {date}')
        return redirect('teacher_attendance_report')
    
    date = request.GET.get('date', timezone.now().date())
    teachers = Teacher.objects.filter(is_active=True)
    
    attendance_records = TeacherAttendance.objects.filter(
        date=date
    ).select_related('teacher')
    
    attendance_dict = {a.teacher_id: a for a in attendance_records}
    
    context = {
        'teachers': teachers,
        'date': date,
        'attendance_dict': attendance_dict,
        'today': timezone.now().date(),
    }
    return render(request, 'teachers/mark_attendance.html', context)

@login_required
def teacher_attendance_report(request):
    """View teacher attendance report"""
    month = request.GET.get('month')
    
    attendance_data = None
    
    if month:
        year, month_num = map(int, month.split('-'))
        
        teachers = Teacher.objects.filter(is_active=True)
        attendance_data = []
        
        for teacher in teachers:
            monthly_attendance = teacher.attendance.filter(
                date__year=year,
                date__month=month_num
            )
            
            total_days = monthly_attendance.count()
            present_days = monthly_attendance.filter(status='present').count()
            absent_days = monthly_attendance.filter(status='absent').count()
            late_days = monthly_attendance.filter(status='late').count()
            leave_days = monthly_attendance.filter(status='on_leave').count()
            
            attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
            
            attendance_data.append({
                'teacher': teacher,
                'total': total_days,
                'present': present_days,
                'absent': absent_days,
                'late': late_days,
                'leave': leave_days,
                'percentage': round(attendance_percentage, 2)
            })
    
    context = {
        'attendance_data': attendance_data,
        'selected_month': month,
    }
    return render(request, 'teachers/attendance_report.html', context)

@login_required
def apply_leave(request):
    """Apply for leave"""
    if request.method == 'POST':
        form = TeacherLeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            
            try:
                teacher = request.user.teacher_profile
                leave.teacher = teacher
                leave.save()
                messages.success(request, 'Leave application submitted successfully!')
                return redirect('my_leaves')
            except Teacher.DoesNotExist:
                messages.error(request, 'Teacher profile not found!')
    else:
        form = TeacherLeaveForm()
    
    return render(request, 'teachers/apply_leave.html', {'form': form})

@login_required
def my_leaves(request):
    """View my leave applications"""
    try:
        teacher = request.user.teacher_profile
        leaves = teacher.leaves.all()
        
        status = request.GET.get('status')
        if status:
            leaves = leaves.filter(status=status)
        
        return render(request, 'teachers/my_leaves.html', {'leaves': leaves})
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found!')
        return redirect('dashboard')

@login_required
def leave_approval(request):
    """Admin view for approving/rejecting leaves"""
    if request.user.role not in ['admin', 'super_admin']:
        messages.error(request, 'You are not authorized to view this page!')
        return redirect('dashboard')
    
    leaves = TeacherLeave.objects.filter(status='pending')
    
    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action')
        
        try:
            leave = TeacherLeave.objects.get(id=leave_id)
            if action == 'approve':
                leave.status = 'approved'
                messages.success(request, f'Leave for {leave.teacher} approved!')
            elif action == 'reject':
                leave.status = 'rejected'
                messages.success(request, f'Leave for {leave.teacher} rejected!')
            
            leave.approved_by = request.user
            leave.approved_on = timezone.now()
            leave.save()
        except TeacherLeave.DoesNotExist:
            messages.error(request, 'Leave not found!')
        
        return redirect('leave_approval')
    
    return render(request, 'teachers/leave_approval.html', {'leaves': leaves})
@login_required
def teacher_attendance_report(request):
    return render(request, 'teachers/attendance_report.html')

@login_required
def apply_leave(request):
    return render(request, 'teachers/apply_leave.html')

@login_required
def my_leaves(request):
    return render(request, 'teachers/my_leaves.html')