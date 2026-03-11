from django.db import models
from core.models import User, AcademicYear
from students.models import Student

class Teacher(models.Model):
    """Teacher Profile"""
    EMPLOYMENT_TYPE = (
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('visiting', 'Visiting'),
        ('probation', 'Probation'),
    )
    
    QUALIFICATION_LEVEL = (
        ('phd', 'PhD'),
        ('masters', 'Masters'),
        ('bachelors', 'Bachelors'),
        ('diploma', 'Diploma'),
        ('certificate', 'Certificate'),
    )
    
    # Link to User account
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    
    # Teacher Information
    employee_id = models.CharField(max_length=20, unique=True)
    joining_date = models.DateField()
    qualification = models.CharField(max_length=200)
    qualification_level = models.CharField(max_length=20, choices=QUALIFICATION_LEVEL, default='bachelors')
    specialization = models.CharField(max_length=100)
    experience_years = models.IntegerField(default=0)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE, default='permanent')
    
    # Class Teacher Assignment
    is_class_teacher = models.BooleanField(default=False)
    assigned_class = models.CharField(max_length=50, blank=True, null=True)
    assigned_section = models.CharField(max_length=10, blank=True, null=True)
    
    # Subjects (many-to-many relationship - we'll create Subject model later)
    subjects = models.CharField(max_length=200, help_text="Comma separated subjects", blank=True)
    
    # Personal Information
    gender = models.CharField(max_length=1, choices=(
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ))
    blood_group = models.CharField(max_length=5, blank=True)
    emergency_contact = models.CharField(max_length=15)
    emergency_contact_name = models.CharField(max_length=100)
    
    # Bank Details (for salary)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_no = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    pan_card = models.CharField(max_length=20, blank=True)
    
    # Salary Information
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Documents
    resume = models.FileField(upload_to='teacher_documents/resume/', blank=True, null=True)
    appointment_letter = models.FileField(upload_to='teacher_documents/appointment/', blank=True, null=True)
    qualification_docs = models.FileField(upload_to='teacher_documents/qualifications/', blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['employee_id']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id}"
    
    def get_full_name(self):
        return self.user.get_full_name()
    
    def get_subjects_list(self):
        """Return subjects as list"""
        if self.subjects:
            return [s.strip() for s in self.subjects.split(',')]
        return []


class TeacherAttendance(models.Model):
    """Daily Teacher Attendance"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=(
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('on_leave', 'On Leave'),
    ), default='present')
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='marked_teacher_attendance')
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['teacher', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.teacher} - {self.date} - {self.status}"


class TeacherLeave(models.Model):
    """Teacher Leave Management"""
    LEAVE_TYPES = (
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('earned', 'Earned Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_on = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_leaves')
    approved_on = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-applied_on']
    
    def __str__(self):
        return f"{self.teacher} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"
    
    @property
    def leave_days(self):
        """Calculate number of leave days"""
        return (self.end_date - self.start_date).days + 1


class TeacherQualification(models.Model):
    """Teacher Qualifications (for multiple qualifications)"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='qualifications')
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=200)
    year_passed = models.IntegerField()
    percentage = models.FloatField(null=True, blank=True)
    division = models.CharField(max_length=50, blank=True)
    certificate = models.FileField(upload_to='teacher_qualifications/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.teacher} - {self.degree} ({self.year_passed})"


class TeacherSubject(models.Model):
    """Subjects taught by teachers (will be used when we create Subject model)"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='teacher_subjects')
    subject_name = models.CharField(max_length=100)
    class_name = models.CharField(max_length=50)
    is_class_teacher = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['teacher', 'subject_name', 'class_name']
    
    def __str__(self):
        return f"{self.teacher} - {self.subject_name} (Class {self.class_name})"
