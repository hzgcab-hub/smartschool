from django.contrib import admin
from .models import Student, StudentAttendance, StudentDocument

class StudentDocumentInline(admin.TabularInline):
    model = StudentDocument
    extra = 1

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'get_full_name', 'current_class', 'section', 'roll_number', 'is_active')
    list_filter = ('current_class', 'section', 'gender', 'is_active')
    search_fields = ('admission_number', 'user__first_name', 'user__last_name', 'user__username')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Student Information', {
            'fields': ('admission_number', 'roll_number', 'current_class', 'section')
        }),
        ('Personal Information', {
            'fields': ('gender', 'blood_group', 'emergency_contact', 'emergency_contact_name')
        }),
        ('Parent Information', {
            'fields': ('father_name', 'father_phone', 'father_occupation', 
                      'mother_name', 'mother_phone', 'mother_occupation')
        }),
        ('Address', {
            'fields': ('present_address', 'permanent_address')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    inlines = [StudentDocumentInline]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'marked_by')
    list_filter = ('status', 'date')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'student__admission_number')
    date_hierarchy = 'date'

@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ('student', 'document_type', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('student__user__first_name', 'student__admission_number')