from django.contrib import admin
from .models import Class, Section, Subject, ClassSubject, Timetable, Homework, HomeworkSubmission

class SectionInline(admin.TabularInline):
    model = Section
    extra = 1

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'numeric_value', 'academic_year', 'class_teacher', 'total_students', 'total_sections', 'is_active')
    list_filter = ('academic_year', 'is_active')
    search_fields = ('name', 'class_teacher__user__first_name')
    list_editable = ('is_active',)
    inlines = [SectionInline]
    
    fieldsets = (
        ('Class Information', {
            'fields': ('name', 'numeric_value', 'academic_year', 'class_teacher', 'room_number', 'capacity')
        }),
        ('Additional Info', {
            'fields': ('description', 'is_active')
        }),
    )

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'class_teacher', 'total_students', 'capacity', 'is_active')
    list_filter = ('class_group__academic_year', 'is_active')
    search_fields = ('name', 'class_group__name', 'class_teacher__user__first_name')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_language', 'is_practical', 'theory_marks', 'practical_marks', 'total_marks', 'is_active')
    list_filter = ('is_language', 'is_practical', 'is_active')
    search_fields = ('name', 'code')

class TimetableInline(admin.TabularInline):
    model = Timetable
    extra = 1

@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('class_group', 'section', 'subject', 'teacher', 'is_mandatory')
    list_filter = ('class_group__academic_year', 'is_mandatory')
    search_fields = ('class_group__name', 'subject__name', 'teacher__user__first_name')
    inlines = [TimetableInline]

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('class_group', 'section', 'day', 'start_time', 'end_time', 'subject', 'teacher')
    list_filter = ('day', 'class_group__academic_year')
    search_fields = ('class_group__name', 'subject__subject__name', 'teacher__user__first_name')

class HomeworkSubmissionInline(admin.TabularInline):
    model = HomeworkSubmission
    extra = 0
    readonly_fields = ('submitted_at',)

@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_group', 'section', 'subject', 'teacher', 'due_date', 'is_active')
    list_filter = ('class_group__academic_year', 'due_date', 'is_active')
    search_fields = ('title', 'description', 'teacher__user__first_name')
    date_hierarchy = 'due_date'
    inlines = [HomeworkSubmissionInline]

@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ('homework', 'student', 'submitted_at', 'marks_obtained', 'graded_by')
    list_filter = ('homework__class_group__academic_year', 'graded_at')
    search_fields = ('student__user__first_name', 'homework__title')
    readonly_fields = ('submitted_at',)
