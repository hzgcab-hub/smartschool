from django.db import models
from core.models import AcademicYear
from teachers.models import Teacher

class Class(models.Model):
    """Class/Grade Level"""
    name = models.CharField(max_length=50)  # e.g., "Class 1", "Grade 10"
    numeric_value = models.IntegerField(help_text="e.g., 1 for Class 1, 10 for Class 10")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='classes')
    class_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='class_teacher_of')
    room_number = models.CharField(max_length=20, blank=True)
    capacity = models.IntegerField(default=40)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['numeric_value']
        unique_together = ['name', 'academic_year']
    
    def __str__(self):
        return f"{self.name} ({self.academic_year})"
    
    @property
    def total_students(self):
        from students.models import Student
        return Student.objects.filter(current_class=self.name, is_active=True).count()
    
    @property
    def total_sections(self):
        return self.sections.count()


class Section(models.Model):
    """Sections within a class"""
    name = models.CharField(max_length=10)  # e.g., "A", "B", "C"
    class_group = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='sections')
    class_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='section_teacher_of')
    room_number = models.CharField(max_length=20, blank=True)
    capacity = models.IntegerField(default=40)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['class_group__numeric_value', 'name']
        unique_together = ['name', 'class_group']
    
    def __str__(self):
        return f"{self.class_group.name} - Section {self.name}"
    
    @property
    def total_students(self):
        from students.models import Student
        return Student.objects.filter(current_class=self.class_group.name, section=self.name, is_active=True).count()


class Subject(models.Model):
    """Subjects taught in school"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_language = models.BooleanField(default=False)
    is_practical = models.BooleanField(default=False)
    theory_marks = models.IntegerField(default=100)
    practical_marks = models.IntegerField(default=0)
    pass_marks = models.IntegerField(default=35)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def total_marks(self):
        return self.theory_marks + self.practical_marks
    
    def save(self, *args, **kwargs):
        if not self.pass_marks:
            self.pass_marks = int(self.total_marks * 0.35)  # 35% passing
        super().save(*args, **kwargs)


class ClassSubject(models.Model):
    """Subjects assigned to specific class"""
    class_group = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='assigned_subjects')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='subjects', null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assigned_classes')
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='teaching_subjects')
    is_mandatory = models.BooleanField(default=True)
    max_students = models.IntegerField(default=0, help_text="0 for unlimited")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['class_group__numeric_value', 'subject__name']
        unique_together = ['class_group', 'section', 'subject']
    
    def __str__(self):
        if self.section:
            return f"{self.class_group.name} - {self.section.name} - {self.subject.name}"
        return f"{self.class_group.name} - {self.subject.name}"


class Timetable(models.Model):
    """Class Timetable"""
    DAYS_OF_WEEK = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    )
    
    class_group = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='timetable')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='timetable')
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='timetable_entries')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='timetable_entries')
    room_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['day', 'start_time']
        unique_together = ['class_group', 'section', 'day', 'start_time']
    
    def __str__(self):
        return f"{self.class_group.name}-{self.section.name} {self.day} {self.start_time}-{self.end_time}"


class Homework(models.Model):
    """Homework assignments"""
    class_group = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='homework')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='homework')
    subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='homework')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='given_homework')
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    attachment = models.FileField(upload_to='homework/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-due_date']
        verbose_name_plural = "Homework"
    
    def __str__(self):
        return f"{self.title} - {self.class_group.name}-{self.section.name}"


class HomeworkSubmission(models.Model):
    """Student homework submissions"""
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='homework_submissions')
    submission_file = models.FileField(upload_to='homework_submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    marks_obtained = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['homework', 'student']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student} - {self.homework.title}"