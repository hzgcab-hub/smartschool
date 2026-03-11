from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import User, AcademicYear

class Student(models.Model):
    """Student Profile"""
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    # Link to User account
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    
    # Student Information
    admission_number = models.CharField(max_length=20, unique=True)
    admission_date = models.DateField(auto_now_add=True)
    roll_number = models.CharField(max_length=10)
    
    # Class Information (we'll create these models next)
    current_class = models.CharField(max_length=50)  # Temporary until we create Class model
    section = models.CharField(max_length=10)  # Temporary until we create Section model
    
    # Personal Information
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=5, blank=True)
    emergency_contact = models.CharField(max_length=15)
    emergency_contact_name = models.CharField(max_length=100)
    
    # Parent/Guardian Information
    father_name = models.CharField(max_length=100)
    father_phone = models.CharField(max_length=15)
    father_occupation = models.CharField(max_length=100, blank=True)
    mother_name = models.CharField(max_length=100)
    mother_phone = models.CharField(max_length=15)
    mother_occupation = models.CharField(max_length=100, blank=True)
    
    # Address (can use from User model or add specific)
    present_address = models.TextField()
    permanent_address = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['current_class', 'section', 'roll_number']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.admission_number}"
    
    def get_full_name(self):
        return self.user.get_full_name()


class StudentAttendance(models.Model):
    """Daily Attendance Tracking"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=(
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
    ), default='present')
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='marked_attendance')
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"


class StudentDocument(models.Model):
    """Student Documents (ID proof, marksheets, etc.)"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=(
        ('birth_certificate', 'Birth Certificate'),
        ('id_proof', 'ID Proof'),
        ('address_proof', 'Address Proof'),
        ('previous_marksheet', 'Previous Marksheet'),
        ('transfer_certificate', 'Transfer Certificate'),
        ('other', 'Other'),
    ))
    document_file = models.FileField(upload_to='student_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.student} - {self.get_document_type_display()}"
