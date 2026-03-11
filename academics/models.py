from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from core.models import AcademicYear, User  # Added User import here
from classes.models import Class, Section, Subject, ClassSubject
from students.models import Student
from teachers.models import Teacher

class Exam(models.Model):
    """Examination details"""
    EXAM_TYPES = (
        ('unit_test', 'Unit Test'),
        ('quarterly', 'Quarterly Exam'),
        ('half_yearly', 'Half Yearly Exam'),
        ('annual', 'Annual Exam'),
        ('pre_board', 'Pre-Board Exam'),
        ('practical', 'Practical Exam'),
        ('oral', 'Oral Exam'),
    )
    
    TERM_CHOICES = (
        ('term1', 'Term 1'),
        ('term2', 'Term 2'),
        ('term3', 'Term 3'),
        ('final', 'Final Term'),
    )
    
    name = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    term = models.CharField(max_length=10, choices=TERM_CHOICES, blank=True, null=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='exams')
    class_group = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='exams')
    description = models.TextField(blank=True)
    
    # Exam Schedule
    start_date = models.DateField()
    end_date = models.DateField()
    result_date = models.DateField(null=True, blank=True)
    
    # Settings
    is_published = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        unique_together = ['name', 'class_group', 'academic_year']
    
    def __str__(self):
        return f"{self.name} - {self.class_group} ({self.academic_year})"
    
    @property
    def total_students(self):
        return Student.objects.filter(current_class=self.class_group.name, is_active=True).count()
    
    @property
    def total_subjects(self):
        return self.exam_subjects.count()
    
    @property
    def results_published(self):
        return self.results.filter(is_published=True).exists()


class ExamSubject(models.Model):
    """Subjects in an exam with marks configuration"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_subjects')
    subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='exam_subjects')
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Marks configuration
    max_marks = models.IntegerField(default=100)
    pass_marks = models.IntegerField(default=35)
    
    # Teacher assigned for evaluation
    evaluator = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='evaluated_exams')
    
    room_number = models.CharField(max_length=20, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['exam_date', 'start_time']
        unique_together = ['exam', 'subject']
    
    def __str__(self):
        return f"{self.exam.name} - {self.subject.subject.name}"
    
    @property
    def total_students_appeared(self):
        return self.marks.filter(is_absent=False).count()
    
    @property
    def passed_students(self):
        return self.marks.filter(is_absent=False, marks_obtained__gte=self.pass_marks).count()


class ExamMark(models.Model):
    """Individual student marks for each exam subject"""
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name='marks')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_marks')
    
    # Marks
    theory_marks = models.FloatField(validators=[MinValueValidator(0)], null=True, blank=True)
    practical_marks = models.FloatField(validators=[MinValueValidator(0)], null=True, blank=True)
    
    # Status
    is_absent = models.BooleanField(default=False)
    is_malpractice = models.BooleanField(default=False)
    
    # Grace marks if any
    grace_marks = models.FloatField(default=0, validators=[MinValueValidator(0)])
    
    # Remarks
    remarks = models.TextField(blank=True)
    
    # Entry tracking
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='entered_marks')
    entered_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['exam_subject', 'student']
        ordering = ['student__roll_number']
    
    def __str__(self):
        return f"{self.student} - {self.exam_subject}"
    
    @property
    def total_marks(self):
        if self.is_absent or self.is_malpractice:
            return 0
        theory = self.theory_marks or 0
        practical = self.practical_marks or 0
        return theory + practical + self.grace_marks
    
    @property
    def percentage(self):
        total_possible = self.exam_subject.max_marks
        if total_possible > 0 and not (self.is_absent or self.is_malpractice):
            return (self.total_marks / total_possible) * 100
        return 0
    
    @property
    def result(self):
        if self.is_absent:
            return 'Absent'
        if self.is_malpractice:
            return 'Malpractice'
        if self.total_marks >= self.exam_subject.pass_marks:
            return 'Pass'
        return 'Fail'


class ExamResult(models.Model):
    """Overall exam result for a student"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    
    # Calculated fields
    total_marks = models.FloatField(default=0)
    percentage = models.FloatField(default=0)
    grade = models.CharField(max_length=5, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    
    # Result status
    is_passed = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    
    # Remarks
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['exam', 'student']
        ordering = ['-percentage']
    
    def __str__(self):
        return f"{self.student} - {self.exam.name} - {self.percentage}%"
    
    def calculate_result(self):
        """Calculate overall result from marks"""
        marks = ExamMark.objects.filter(
            exam_subject__exam=self.exam,
            student=self.student
        )
        
        total_obtained = 0
        total_max = 0
        failed_subjects = 0
        total_subjects = marks.count()
        
        for mark in marks:
            if not (mark.is_absent or mark.is_malpractice):
                total_obtained += mark.total_marks
                total_max += mark.exam_subject.max_marks
                
                if mark.total_marks < mark.exam_subject.pass_marks:
                    failed_subjects += 1
            else:
                failed_subjects += 1
        
        self.total_marks = total_obtained
        if total_max > 0:
            self.percentage = (total_obtained / total_max) * 100
        
        self.is_passed = failed_subjects == 0
        
        # Calculate grade (customize based on your grading system)
        if self.percentage >= 90:
            self.grade = 'A+'
        elif self.percentage >= 80:
            self.grade = 'A'
        elif self.percentage >= 70:
            self.grade = 'B+'
        elif self.percentage >= 60:
            self.grade = 'B'
        elif self.percentage >= 50:
            self.grade = 'C'
        elif self.percentage >= 40:
            self.grade = 'D'
        else:
            self.grade = 'F'
        
        self.save()


class GradeSystem(models.Model):
    """Grading system configuration"""
    name = models.CharField(max_length=50)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='grade_systems')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class GradeRange(models.Model):
    """Individual grade ranges"""
    grade_system = models.ForeignKey(GradeSystem, on_delete=models.CASCADE, related_name='ranges')
    grade = models.CharField(max_length=5)
    min_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    grade_point = models.FloatField(null=True, blank=True)
    description = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-min_percentage']
        unique_together = ['grade_system', 'grade']
    
    def __str__(self):
        return f"{self.grade} ({self.min_percentage}-{self.max_percentage}%)"


class ReportCard(models.Model):
    """Student report card"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='report_cards')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='report_cards')
    result = models.OneToOneField(ExamResult, on_delete=models.CASCADE, related_name='report_card')
    
    # PDF file
    pdf_file = models.FileField(upload_to='report_cards/', blank=True, null=True)
    
    # Generated by
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_reports')
    generated_at = models.DateTimeField(auto_now_add=True)
    
    # Download count
    download_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['student', 'exam']
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Report Card - {self.student} - {self.exam.name}"