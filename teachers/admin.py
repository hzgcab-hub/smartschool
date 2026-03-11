from django.contrib import admin
from .models import Teacher, TeacherAttendance, TeacherLeave, TeacherQualification, TeacherSubject

class TeacherQualificationInline(admin.TabularInline):
    model = TeacherQualification
    extra = 1

class TeacherSubjectInline(admin.TabularInline):
    model = TeacherSubject
    extra = 2

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'get_full_name', 'qualification_level', 'employment_type', 'is_class_teacher', 'is_active')
    list_filter = ('qualification_level', 'employment_type', 'is_class_teacher', 'gender', 'is_active')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name', 'user__email', 'specialization')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Employee Information', {
            'fields': ('employee_id', 'joining_date', 'employment_type', 'experience_years')
        }),
        ('Professional Information', {
            'fields': ('qualification', 'qualification_level', 'specialization', 'subjects')
        }),
        ('Class Teacher Assignment', {
            'fields': ('is_class_teacher', 'assigned_class', 'assigned_section'),
            'classes': ('collapse',),
        }),
        ('Personal Information', {
            'fields': ('gender', 'blood_group', 'emergency_contact', 'emergency_contact_name')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'bank_account_no', 'ifsc_code', 'pan_card'),
            'classes': ('collapse',),
        }),
        ('Salary Information', {
            'fields': ('salary',),
            'classes': ('collapse',),
        }),
        ('Documents', {
            'fields': ('resume', 'appointment_letter', 'qualification_docs'),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    inlines = [TeacherQualificationInline, TeacherSubjectInline]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'

@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'date', 'status', 'check_in_time', 'check_out_time', 'marked_by')
    list_filter = ('status', 'date')
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name', 'teacher__employee_id')
    date_hierarchy = 'date'

@admin.register(TeacherLeave)
class TeacherLeaveAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'leave_type', 'start_date', 'end_date', 'leave_days', 'status', 'applied_on')
    list_filter = ('leave_type', 'status', 'start_date')
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name', 'reason')
    actions = ['approve_leaves', 'reject_leaves']
    
    def approve_leaves(self, request, queryset):
        queryset.update(status='approved', approved_by=request.user, approved_on=datetime.now())
    approve_leaves.short_description = "Approve selected leaves"
    
    def reject_leaves(self, request, queryset):
        queryset.update(status='rejected', approved_by=request.user, approved_on=datetime.now())
    reject_leaves.short_description = "Reject selected leaves"

@admin.register(TeacherQualification)
class TeacherQualificationAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'degree', 'institution', 'year_passed', 'percentage')
    list_filter = ('year_passed', 'degree')
    search_fields = ('teacher__user__first_name', 'degree', 'institution')

@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject_name', 'class_name', 'is_class_teacher')
    list_filter = ('subject_name', 'class_name', 'is_class_teacher')
    search_fields = ('teacher__user__first_name', 'subject_name')
