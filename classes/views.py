from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Class, Section, Subject, ClassSubject, Timetable, Homework, HomeworkSubmission
from .forms import (
    ClassForm, SectionForm, SubjectForm, ClassSubjectForm, 
    TimetableForm, HomeworkForm, HomeworkSubmissionForm,
    HomeworkGradingForm
)

# ========== Class Views ==========
@login_required
def class_list(request):
    """View all classes"""
    classes = Class.objects.filter(is_active=True)
    
    # Search
    query = request.GET.get('q')
    if query:
        classes = classes.filter(
            Q(name__icontains=query) |
            Q(class_teacher__user__first_name__icontains=query) |
            Q(class_teacher__user__last_name__icontains=query)
        )
    
    # Filter by academic year
    year = request.GET.get('academic_year')
    if year:
        classes = classes.filter(academic_year_id=year)
    
    paginator = Paginator(classes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'classes/class_list.html', context)

@login_required
def class_detail(request, pk):
    """View single class details"""
    class_obj = get_object_or_404(Class, pk=pk)
    sections = class_obj.sections.filter(is_active=True)
    subjects = class_obj.assigned_subjects.all()
    timetable = class_obj.timetable.all().order_by('day', 'start_time')
    homework = class_obj.homework.filter(is_active=True)[:10]
    
    from students.models import Student
    students = Student.objects.filter(current_class=class_obj.name, is_active=True)
    
    context = {
        'class_obj': class_obj,
        'sections': sections,
        'subjects': subjects,
        'timetable': timetable,
        'homework': homework,
        'students': students,
        'student_count': students.count(),
    }
    return render(request, 'classes/class_detail.html', context)

@login_required
def class_create(request):
    """Create new class"""
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            class_obj = form.save()
            messages.success(request, f'Class {class_obj.name} created successfully!')
            return redirect('class_detail', pk=class_obj.pk)
    else:
        form = ClassForm()
    
    return render(request, 'classes/class_form.html', {
        'form': form, 
        'title': 'Add New Class'
    })

@login_required
def class_edit(request, pk):
    """Edit class"""
    class_obj = get_object_or_404(Class, pk=pk)
    
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class updated successfully!')
            return redirect('class_detail', pk=class_obj.pk)
    else:
        form = ClassForm(instance=class_obj)
    
    return render(request, 'classes/class_form.html', {
        'form': form, 
        'title': f'Edit {class_obj.name}'
    })

@login_required
def class_delete(request, pk):
    """Delete class"""
    class_obj = get_object_or_404(Class, pk=pk)
    
    if request.method == 'POST':
        class_obj.is_active = False
        class_obj.save()
        messages.success(request, 'Class deactivated successfully!')
        return redirect('class_list')
    
    return render(request, 'classes/class_confirm_delete.html', {'class_obj': class_obj})

# ========== Section Views ==========
@login_required
def section_list(request):
    """View all sections"""
    sections = Section.objects.filter(is_active=True)
    
    query = request.GET.get('q')
    if query:
        sections = sections.filter(
            Q(name__icontains=query) |
            Q(class_group__name__icontains=query) |
            Q(class_teacher__user__first_name__icontains=query)
        )
    
    paginator = Paginator(sections, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj, 'query': query}
    return render(request, 'classes/section_list.html', context)

@login_required
def section_create(request):
    """Create new section"""
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            section = form.save()
            messages.success(request, f'Section {section} created successfully!')
            return redirect('class_detail', pk=section.class_group.pk)
    else:
        form = SectionForm()
    
    return render(request, 'classes/section_form.html', {
        'form': form, 
        'title': 'Add New Section'
    })

@login_required
def section_edit(request, pk):
    """Edit section"""
    section = get_object_or_404(Section, pk=pk)
    
    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, 'Section updated successfully!')
            return redirect('class_detail', pk=section.class_group.pk)
    else:
        form = SectionForm(instance=section)
    
    return render(request, 'classes/section_form.html', {
        'form': form, 
        'title': f'Edit {section}'
    })

@login_required
def section_delete(request, pk):
    """Delete section"""
    section = get_object_or_404(Section, pk=pk)
    class_pk = section.class_group.pk
    
    if request.method == 'POST':
        section.is_active = False
        section.save()
        messages.success(request, 'Section deactivated successfully!')
        return redirect('class_detail', pk=class_pk)
    
    return render(request, 'classes/section_confirm_delete.html', {'section': section})

# ========== Subject Views ==========
@login_required
def subject_list(request):
    """View all subjects"""
    subjects = Subject.objects.filter(is_active=True)
    
    query = request.GET.get('q')
    if query:
        subjects = subjects.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query)
        )
    
    paginator = Paginator(subjects, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj, 'query': query}
    return render(request, 'classes/subject_list.html', context)

@login_required
def subject_create(request):
    """Create new subject"""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject {subject.name} created successfully!')
            return redirect('subject_list')
    else:
        form = SubjectForm()
    
    return render(request, 'classes/subject_form.html', {
        'form': form, 
        'title': 'Add New Subject'
    })

@login_required
def subject_edit(request, pk):
    """Edit subject"""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated successfully!')
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'classes/subject_form.html', {
        'form': form, 
        'title': f'Edit {subject.name}'
    })

@login_required
def subject_delete(request, pk):
    """Delete subject"""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        subject.is_active = False
        subject.save()
        messages.success(request, 'Subject deactivated successfully!')
        return redirect('subject_list')
    
    return render(request, 'classes/subject_confirm_delete.html', {'subject': subject})

# ========== Timetable Views ==========
@login_required
def timetable_view(request, class_id=None, section_id=None):
    """View timetable"""
    if class_id:
        class_obj = get_object_or_404(Class, pk=class_id)
        sections = class_obj.sections.filter(is_active=True)
        
        if section_id:
            section = get_object_or_404(Section, pk=section_id)
            timetable = Timetable.objects.filter(
                class_group=class_obj, 
                section=section,
                is_active=True
            ).order_by('day', 'start_time')
        else:
            section = None
            timetable = Timetable.objects.filter(
                class_group=class_obj,
                is_active=True
            ).order_by('day', 'start_time')
        
        # Group by day
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        timetable_by_day = {}
        for day in days:
            timetable_by_day[day] = timetable.filter(day=day)
        
        context = {
            'class_obj': class_obj,
            'section': section,
            'sections': sections,
            'timetable_by_day': timetable_by_day,
            'days': days,
        }
        return render(request, 'classes/timetable_view.html', context)
    
    # Show class selection
    classes = Class.objects.filter(is_active=True)
    return render(request, 'classes/timetable_select.html', {'classes': classes})

@login_required
def timetable_add(request):
    """Add timetable entry"""
    if request.method == 'POST':
        form = TimetableForm(request.POST)
        if form.is_valid():
            timetable = form.save()
            messages.success(request, 'Timetable entry added successfully!')
            return redirect('timetable_view', class_id=timetable.class_group.pk, section_id=timetable.section.pk if timetable.section else None)
    else:
        form = TimetableForm()
    
    return render(request, 'classes/timetable_form.html', {
        'form': form, 
        'title': 'Add Timetable Entry'
    })

# ========== Homework Views ==========
@login_required
def homework_list(request):
    """View all homework"""
    homework = Homework.objects.filter(is_active=True)
    
    query = request.GET.get('q')
    if query:
        homework = homework.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(teacher__user__first_name__icontains=query)
        )
    
    # Filter by class
    class_id = request.GET.get('class')
    if class_id:
        homework = homework.filter(class_group_id=class_id)
    
    paginator = Paginator(homework, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    classes = Class.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'classes': classes,
        'query': query,
        'class_id': class_id,
    }
    return render(request, 'classes/homework_list.html', context)

@login_required
def homework_detail(request, pk):
    """View homework details"""
    homework = get_object_or_404(Homework, pk=pk)
    
    # Check if user is teacher for this homework
    is_teacher = False
    if hasattr(request.user, 'teacher_profile'):
        is_teacher = homework.teacher == request.user.teacher_profile
    
    # Get submissions
    submissions = homework.submissions.all() if is_teacher else homework.submissions.filter(student__user=request.user)
    
    context = {
        'homework': homework,
        'submissions': submissions,
        'is_teacher': is_teacher,
        'can_submit': not submissions.exists() and hasattr(request.user, 'student_profile'),
    }
    return render(request, 'classes/homework_detail.html', context)

@login_required
def homework_create(request):
    """Create new homework"""
    if request.method == 'POST':
        form = HomeworkForm(request.POST, request.FILES)
        if form.is_valid():
            homework = form.save(commit=False)
            
            # Set teacher from logged in user
            if hasattr(request.user, 'teacher_profile'):
                homework.teacher = request.user.teacher_profile
                homework.save()
                messages.success(request, 'Homework created successfully!')
                return redirect('homework_detail', pk=homework.pk)
            else:
                messages.error(request, 'Only teachers can create homework!')
    else:
        form = HomeworkForm()
    
    return render(request, 'classes/homework_form.html', {
        'form': form, 
        'title': 'Create New Homework'
    })

@login_required
def homework_submit(request, pk):
    """Submit homework"""
    homework = get_object_or_404(Homework, pk=pk)
    
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Only students can submit homework!')
        return redirect('homework_detail', pk=pk)
    
    # Check if already submitted
    if HomeworkSubmission.objects.filter(homework=homework, student=request.user.student_profile).exists():
        messages.error(request, 'You have already submitted this homework!')
        return redirect('homework_detail', pk=pk)
    
    if request.method == 'POST':
        form = HomeworkSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.homework = homework
            submission.student = request.user.student_profile
            submission.save()
            messages.success(request, 'Homework submitted successfully!')
            return redirect('homework_detail', pk=pk)
    else:
        form = HomeworkSubmissionForm()
    
    return render(request, 'classes/homework_submit.html', {
        'form': form,
        'homework': homework
    })

@login_required
def homework_grade(request, pk):
    """Grade homework submission"""
    submission = get_object_or_404(HomeworkSubmission, pk=pk)
    
    # Check if user is the teacher for this homework
    if not hasattr(request.user, 'teacher_profile') or submission.homework.teacher != request.user.teacher_profile:
        messages.error(request, 'You are not authorized to grade this submission!')
        return redirect('homework_detail', pk=submission.homework.pk)
    
    if request.method == 'POST':
        form = HomeworkGradingForm(request.POST, instance=submission)
        if form.is_valid():
            graded_submission = form.save(commit=False)
            graded_submission.graded_by = request.user.teacher_profile
            graded_submission.graded_at = timezone.now()
            graded_submission.save()
            messages.success(request, 'Homework graded successfully!')
            return redirect('homework_detail', pk=submission.homework.pk)
    else:
        form = HomeworkGradingForm(instance=submission)
    
    return render(request, 'classes/homework_grade.html', {
        'form': form,
        'submission': submission
    })
# Simple placeholder views for missing functionality
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def subject_create(request):
    return render(request, 'classes/subject_form.html', {'title': 'Add Subject'})

@login_required
def subject_edit(request, pk):
    return render(request, 'classes/subject_form.html', {'title': 'Edit Subject'})

@login_required
def subject_delete(request, pk):
    return render(request, 'classes/subject_confirm_delete.html')

@login_required
def section_create(request):
    return render(request, 'classes/section_form.html', {'title': 'Add Section'})

@login_required
def section_edit(request, pk):
    return render(request, 'classes/section_form.html', {'title': 'Edit Section'})