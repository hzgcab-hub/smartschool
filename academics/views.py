from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Sum, Count
from django.db import transaction
from django.utils import timezone
from .models import (
    Exam, ExamSubject, ExamMark, ExamResult,
    GradeSystem, GradeRange, ReportCard
)
from classes.models import Class, ClassSubject
from students.models import Student
from teachers.models import Teacher
from .forms import (
    ExamForm, ExamSubjectForm, MarksEntryForm,
    SingleMarkEntryForm, GradeSystemForm,
    GradeRangeForm, ResultPublishForm
)
import json

# ========== Exam Views ==========
@login_required
def exam_list(request):
    """View all exams"""
    exams = Exam.objects.filter(is_active=True)
    
    # Search
    query = request.GET.get('q')
    if query:
        exams = exams.filter(
            Q(name__icontains=query) |
            Q(class_group__name__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Filter by class
    class_id = request.GET.get('class')
    if class_id:
        exams = exams.filter(class_group_id=class_id)
    
    # Filter by exam type
    exam_type = request.GET.get('type')
    if exam_type:
        exams = exams.filter(exam_type=exam_type)
    
    paginator = Paginator(exams, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    classes = Class.objects.filter(is_active=True)
    exam_types = Exam.EXAM_TYPES
    
    context = {
        'page_obj': page_obj,
        'classes': classes,
        'exam_types': exam_types,
        'query': query,
        'class_id': class_id,
        'exam_type': exam_type,
    }
    return render(request, 'academics/exam_list.html', context)

@login_required
def exam_detail(request, pk):
    """View exam details"""
    exam = get_object_or_404(Exam, pk=pk)
    subjects = exam.exam_subjects.all().order_by('exam_date', 'start_time')
    
    # Get results summary
    results = ExamResult.objects.filter(exam=exam)
    total_students = Student.objects.filter(current_class=exam.class_group.name, is_active=True).count()
    results_published = results.filter(is_published=True).count()
    passed_count = results.filter(is_passed=True).count()
    
    context = {
        'exam': exam,
        'subjects': subjects,
        'total_students': total_students,
        'results_published': results_published,
        'passed_count': passed_count,
        'total_results': results.count(),
    }
    return render(request, 'academics/exam_detail.html', context)

@login_required
def exam_create(request):
    """Create new exam"""
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save()
            messages.success(request, f'Exam {exam.name} created successfully!')
            return redirect('exam_detail', pk=exam.pk)
    else:
        form = ExamForm()
    
    return render(request, 'academics/exam_form.html', {
        'form': form,
        'title': 'Create New Exam'
    })

@login_required
def exam_edit(request, pk):
    """Edit exam"""
    exam = get_object_or_404(Exam, pk=pk)
    
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam updated successfully!')
            return redirect('exam_detail', pk=exam.pk)
    else:
        form = ExamForm(instance=exam)
    
    return render(request, 'academics/exam_form.html', {
        'form': form,
        'title': f'Edit {exam.name}'
    })

@login_required
def exam_delete(request, pk):
    """Delete exam"""
    exam = get_object_or_404(Exam, pk=pk)
    
    if request.method == 'POST':
        exam.is_active = False
        exam.save()
        messages.success(request, 'Exam deactivated successfully!')
        return redirect('exam_list')
    
    return render(request, 'academics/exam_confirm_delete.html', {'exam': exam})

# ========== Exam Subject Views ==========
@login_required
def exam_subject_add(request, exam_id):
    """Add subject to exam"""
    exam = get_object_or_404(Exam, pk=exam_id)
    
    if request.method == 'POST':
        form = ExamSubjectForm(request.POST)
        if form.is_valid():
            exam_subject = form.save(commit=False)
            exam_subject.exam = exam
            exam_subject.save()
            messages.success(request, 'Subject added to exam successfully!')
            return redirect('exam_detail', pk=exam.pk)
    else:
        form = ExamSubjectForm(initial={'exam': exam})
        form.fields['subject'].queryset = ClassSubject.objects.filter(class_group=exam.class_group)
    
    return render(request, 'academics/exam_subject_form.html', {
        'form': form,
        'exam': exam,
        'title': f'Add Subject to {exam.name}'
    })

@login_required
def exam_subject_edit(request, pk):
    """Edit exam subject"""
    exam_subject = get_object_or_404(ExamSubject, pk=pk)
    
    if request.method == 'POST':
        form = ExamSubjectForm(request.POST, instance=exam_subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam subject updated successfully!')
            return redirect('exam_detail', pk=exam_subject.exam.pk)
    else:
        form = ExamSubjectForm(instance=exam_subject)
    
    return render(request, 'academics/exam_subject_form.html', {
        'form': form,
        'exam': exam_subject.exam,
        'title': f'Edit {exam_subject.subject.subject.name}'
    })

@login_required
def exam_subject_delete(request, pk):
    """Delete exam subject"""
    exam_subject = get_object_or_404(ExamSubject, pk=pk)
    exam_id = exam_subject.exam.pk
    
    if request.method == 'POST':
        exam_subject.delete()
        messages.success(request, 'Subject removed from exam successfully!')
        return redirect('exam_detail', pk=exam_id)
    
    return render(request, 'academics/exam_subject_confirm_delete.html', {'exam_subject': exam_subject})

# ========== Marks Entry Views ==========
@login_required
def marks_entry(request, exam_subject_id):
    """Enter marks for an exam subject"""
    exam_subject = get_object_or_404(ExamSubject, pk=exam_subject_id)
    
    # Get students in this class
    students = Student.objects.filter(
        current_class=exam_subject.exam.class_group.name,
        is_active=True
    ).order_by('roll_number')
    
    if request.method == 'POST':
        form = MarksEntryForm(request.POST, students=students, exam_subject=exam_subject)
        
        if form.is_valid():
            with transaction.atomic():
                for student in students:
                    prefix = f"student_{student.id}"
                    theory = form.cleaned_data.get(f"{prefix}_theory")
                    practical = form.cleaned_data.get(f"{prefix}_practical")
                    is_absent = form.cleaned_data.get(f"{prefix}_absent", False)
                    is_malpractice = form.cleaned_data.get(f"{prefix}_malpractice", False)
                    remarks = form.cleaned_data.get(f"{prefix}_remarks", "")
                    
                    # Create or update mark
                    mark, created = ExamMark.objects.update_or_create(
                        exam_subject=exam_subject,
                        student=student,
                        defaults={
                            'theory_marks': theory,
                            'practical_marks': practical,
                            'is_absent': is_absent,
                            'is_malpractice': is_malpractice,
                            'remarks': remarks,
                            'entered_by': request.user
                        }
                    )
            
            # Mark subject as completed
            exam_subject.is_completed = True
            exam_subject.save()
            
            messages.success(request, 'Marks entered successfully!')
            return redirect('exam_detail', pk=exam_subject.exam.pk)
    else:
        form = MarksEntryForm(students=students, exam_subject=exam_subject)
        
        # Pre-fill existing marks
        existing_marks = ExamMark.objects.filter(exam_subject=exam_subject)
        for mark in existing_marks:
            prefix = f"student_{mark.student.id}"
            form.fields[f"{prefix}_theory"].initial = mark.theory_marks
            form.fields[f"{prefix}_practical"].initial = mark.practical_marks
            form.fields[f"{prefix}_absent"].initial = mark.is_absent
            form.fields[f"{prefix}_malpractice"].initial = mark.is_malpractice
            form.fields[f"{prefix}_remarks"].initial = mark.remarks
    
    context = {
        'form': form,
        'exam_subject': exam_subject,
        'students': students,
        'title': f'Enter Marks - {exam_subject.subject.subject.name}'
    }
    return render(request, 'academics/marks_entry.html', context)

@login_required
def marks_entry_single(request, exam_subject_id, student_id):
    """Enter marks for a single student"""
    exam_subject = get_object_or_404(ExamSubject, pk=exam_subject_id)
    student = get_object_or_404(Student, pk=student_id)
    
    mark, created = ExamMark.objects.get_or_create(
        exam_subject=exam_subject,
        student=student,
        defaults={'entered_by': request.user}
    )
    
    if request.method == 'POST':
        form = SingleMarkEntryForm(request.POST, instance=mark)
        if form.is_valid():
            mark = form.save(commit=False)
            mark.entered_by = request.user
            mark.save()
            messages.success(request, f'Marks for {student.user.get_full_name()} saved!')
            return redirect('marks_entry', exam_subject_id=exam_subject.pk)
    else:
        form = SingleMarkEntryForm(instance=mark)
    
    context = {
        'form': form,
        'exam_subject': exam_subject,
        'student': student,
    }
    return render(request, 'academics/marks_entry_single.html', context)

# ========== Result Views ==========
@login_required
def generate_results(request, exam_id):
    """Generate results for all students"""
    exam = get_object_or_404(Exam, pk=exam_id)
    
    if request.method == 'POST':
        students = Student.objects.filter(current_class=exam.class_group.name, is_active=True)
        
        with transaction.atomic():
            for student in students:
                # Check if all subjects have marks
                total_subjects = exam.exam_subjects.count()
                marks_count = ExamMark.objects.filter(
                    exam_subject__exam=exam,
                    student=student
                ).count()
                
                if total_subjects == marks_count:
                    # Create or update result
                    result, created = ExamResult.objects.update_or_create(
                        exam=exam,
                        student=student,
                        defaults={'is_published': False}
                    )
                    result.calculate_result()
            
            messages.success(request, 'Results generated successfully!')
        
        return redirect('exam_results', exam_id=exam.pk)
    
    context = {
        'exam': exam,
    }
    return render(request, 'academics/generate_results.html', context)

@login_required
def exam_results(request, exam_id):
    """View exam results"""
    exam = get_object_or_404(Exam, pk=exam_id)
    results = ExamResult.objects.filter(exam=exam).order_by('-percentage')
    
    # Filter by section
    section = request.GET.get('section')
    if section:
        results = results.filter(student__section=section)
    
    # Search
    query = request.GET.get('q')
    if query:
        results = results.filter(
            Q(student__user__first_name__icontains=query) |
            Q(student__user__last_name__icontains=query) |
            Q(student__admission_number__icontains=query)
        )
    
    paginator = Paginator(results, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_students = results.count()
    passed = results.filter(is_passed=True).count()
    failed = total_students - passed
    pass_percentage = (passed / total_students * 100) if total_students > 0 else 0
    average_percentage = results.aggregate(Avg('percentage'))['percentage__avg'] or 0
    
    context = {
        'exam': exam,
        'page_obj': page_obj,
        'total_students': total_students,
        'passed': passed,
        'failed': failed,
        'pass_percentage': round(pass_percentage, 2),
        'average_percentage': round(average_percentage, 2),
        'query': query,
        'section': section,
    }
    return render(request, 'academics/exam_results.html', context)

@login_required
def student_result_detail(request, result_id):
    """View individual student result"""
    result = get_object_or_404(ExamResult, pk=result_id)
    marks = ExamMark.objects.filter(
        exam_subject__exam=result.exam,
        student=result.student
    ).select_related('exam_subject__subject__subject')
    
    context = {
        'result': result,
        'marks': marks,
    }
    return render(request, 'academics/student_result_detail.html', context)

@login_required
def publish_results(request, exam_id):
    """Publish/unpublish exam results"""
    exam = get_object_or_404(Exam, pk=exam_id)
    
    if request.method == 'POST':
        form = ResultPublishForm(request.POST)
        if form.is_valid():
            publish = form.cleaned_data['publish']
            
            # Update all results
            ExamResult.objects.filter(exam=exam).update(is_published=publish)
            
            # Update exam
            exam.is_published = publish
            exam.save()
            
            action = "published" if publish else "unpublished"
            messages.success(request, f'Results {action} successfully!')
            
            return redirect('exam_results', exam_id=exam.pk)
    else:
        form = ResultPublishForm(initial={'publish': not exam.is_published})
    
    context = {
        'form': form,
        'exam': exam,
    }
    return render(request, 'academics/publish_results.html', context)

# ========== Grade System Views ==========
@login_required
def grade_system_list(request):
    """View all grade systems"""
    grade_systems = GradeSystem.objects.filter(is_active=True)
    
    context = {
        'grade_systems': grade_systems,
    }
    return render(request, 'academics/grade_system_list.html', context)

@login_required
def grade_system_create(request):
    """Create new grade system"""
    if request.method == 'POST':
        form = GradeSystemForm(request.POST)
        if form.is_valid():
            grade_system = form.save()
            messages.success(request, 'Grade system created successfully!')
            return redirect('grade_system_list')
    else:
        form = GradeSystemForm()
    
    return render(request, 'academics/grade_system_form.html', {
        'form': form,
        'title': 'Create Grade System'
    })

@login_required
def grade_system_edit(request, pk):
    """Edit grade system"""
    grade_system = get_object_or_404(GradeSystem, pk=pk)
    
    if request.method == 'POST':
        form = GradeSystemForm(request.POST, instance=grade_system)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grade system updated successfully!')
            return redirect('grade_system_list')
    else:
        form = GradeSystemForm(instance=grade_system)
    
    return render(request, 'academics/grade_system_form.html', {
        'form': form,
        'title': f'Edit {grade_system.name}'
    })

# ========== Report Card Views ==========
@login_required
def generate_report_card(request, result_id):
    """Generate PDF report card"""
    result = get_object_or_404(ExamResult, pk=result_id)
    
    # Check if report card already exists
    report_card, created = ReportCard.objects.get_or_create(
        student=result.student,
        exam=result.exam,
        result=result,
        defaults={'generated_by': request.user}
    )
    
    # Here you would generate PDF using reportlab or WeasyPrint
    # For now, we'll just show a success message
    
    messages.success(request, 'Report card generated successfully!')
    return redirect('student_result_detail', result_id=result.pk)

@login_required
def download_report_card(request, pk):
    """Download report card PDF"""
    report_card = get_object_or_404(ReportCard, pk=pk)
    
    # Increment download count
    report_card.download_count += 1
    report_card.save()
    
    # Here you would serve the PDF file
    # For now, redirect back
    
    messages.success(request, 'Report card downloaded!')
    return redirect('student_result_detail', result_id=report_card.result.pk)