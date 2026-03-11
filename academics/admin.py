from django.contrib import admin
from .models import (
    Exam, ExamSubject, ExamMark, ExamResult, 
    GradeSystem, GradeRange, ReportCard
)

class ExamSubjectInline(admin.TabularInline):
    model = ExamSubject
    extra = 1

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'class_group', 'academic_year', 'start_date', 'end_date', 'is_published')
    list_filter = ('exam_type', 'academic_year', 'is_published', 'class_group')
    search_fields = ('name', 'class_group__name')
    date_hierarchy = 'start_date'
    inlines = [ExamSubjectInline]
    
    fieldsets = (
        ('Exam Information', {
            'fields': ('name', 'exam_type', 'term', 'academic_year', 'class_group', 'description')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'result_date')
        }),
        ('Status', {
            'fields': ('is_published', 'is_active')
        }),
    )

class ExamMarkInline(admin.TabularInline):
    model = ExamMark
    extra = 0
    fields = ('student', 'theory_marks', 'practical_marks', 'is_absent', 'is_malpractice', 'grace_marks', 'remarks')
    readonly_fields = ('student',)

@admin.register(ExamSubject)
class ExamSubjectAdmin(admin.ModelAdmin):
    list_display = ('exam', 'subject', 'exam_date', 'start_time', 'end_time', 'max_marks', 'pass_marks', 'is_completed')
    list_filter = ('exam__academic_year', 'is_completed')
    search_fields = ('exam__name', 'subject__subject__name')
    inlines = [ExamMarkInline]

@admin.register(ExamMark)
class ExamMarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam_subject', 'theory_marks', 'practical_marks', 'total_marks', 'result', 'is_absent')
    list_filter = ('exam_subject__exam', 'is_absent', 'is_malpractice')
    search_fields = ('student__user__first_name', 'student__admission_number')
    readonly_fields = ('total_marks', 'percentage', 'result')

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'total_marks', 'percentage', 'grade', 'rank', 'is_passed', 'is_published')
    list_filter = ('exam', 'is_passed', 'is_published')
    search_fields = ('student__user__first_name', 'student__admission_number')

class GradeRangeInline(admin.TabularInline):
    model = GradeRange
    extra = 1

@admin.register(GradeSystem)
class GradeSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'is_active')
    list_filter = ('academic_year', 'is_active')
    inlines = [GradeRangeInline]

@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'generated_at', 'download_count')
    list_filter = ('exam__academic_year',)
    search_fields = ('student__user__first_name', 'student__admission_number')
    readonly_fields = ('generated_at', 'download_count')
