from django.db import models
from django.utils import timezone
from core.models import User
from classes.models import Class
from students.models import Student
from teachers.models import Teacher

class NoticeCategory(models.Model):
    """Categories for notices"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, default='blue', help_text="Bootstrap color class")
    icon = models.CharField(max_length=50, default='fa-bullhorn', help_text="Font Awesome icon class")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Notice Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Notice(models.Model):
    """School notices and announcements"""
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    
    AUDIENCE_CHOICES = (
        ('all', 'Everyone'),
        ('students', 'All Students'),
        ('teachers', 'All Teachers'),
        ('parents', 'All Parents'),
        ('staff', 'All Staff'),
        ('specific', 'Specific Classes'),
    )
    
    # Basic Information
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.ForeignKey(NoticeCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='notices')
    
    # Priority & Status
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Author
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='authored_notices')
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    publish_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Audience
    audience_type = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all')
    target_classes = models.ManyToManyField(Class, blank=True, related_name='targeted_notices')
    target_students = models.ManyToManyField(Student, blank=True, related_name='targeted_notices')
    target_teachers = models.ManyToManyField(Teacher, blank=True, related_name='targeted_notices')
    
    # Media
    attachment = models.FileField(upload_to='notice_attachments/', blank=True, null=True)
    image = models.ImageField(upload_to='notice_images/', blank=True, null=True)
    
    # Settings
    is_pinned = models.BooleanField(default=False, help_text="Pin to top of list")
    requires_acknowledgment = models.BooleanField(default=False, help_text="Users must acknowledge reading this")
    send_email = models.BooleanField(default=False, help_text="Send email notification")
    send_sms = models.BooleanField(default=False, help_text="Send SMS notification")
    send_push = models.BooleanField(default=False, help_text="Send push notification")
    
    # View tracking
    view_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-is_pinned', '-publish_date', '-created_at']
    
    def __str__(self):
        return self.title
    
    def is_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False
    
    def is_published(self):
        return self.status == 'published' and not self.is_expired()
    
    def can_view(self, user):
        """Check if user can view this notice"""
        if user.role == 'super_admin' or user.role == 'admin':
            return True
        
        if self.audience_type == 'all':
            return True
        
        if self.audience_type == 'students' and user.role == 'student':
            return True
        
        if self.audience_type == 'teachers' and user.role == 'teacher':
            return True
        
        if self.audience_type == 'parents' and user.role == 'parent':
            return True
        
        if self.audience_type == 'specific':
            # Check if user is in target classes
            if user.role == 'student' and hasattr(user, 'student_profile'):
                return self.target_classes.filter(name=user.student_profile.current_class).exists()
            
            if user.role == 'teacher' and hasattr(user, 'teacher_profile'):
                return self.target_teachers.filter(id=user.teacher_profile.id).exists()
        
        return False


class NoticeAcknowledgement(models.Model):
    """Track who has acknowledged notices"""
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='acknowledgements')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notice_acknowledgements')
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['notice', 'user']
        ordering = ['-acknowledged_at']
    
    def __str__(self):
        return f"{self.user.username} acknowledged {self.notice.title}"


class NoticeView(models.Model):
    """Track notice views"""
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notice_views')
    viewed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = ['notice', 'user']
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.user.username} viewed {self.notice.title}"


class Circular(models.Model):
    """Official circulars/documents"""
    CIRCULAR_TYPES = (
        ('office_order', 'Office Order'),
        ('memo', 'Memo'),
        ('circular', 'Circular'),
        ('notification', 'Notification'),
        ('government_order', 'Government Order'),
    )
    
    title = models.CharField(max_length=200)
    circular_number = models.CharField(max_length=50, unique=True)
    circular_type = models.CharField(max_length=20, choices=CIRCULAR_TYPES)
    
    # Dates
    issue_date = models.DateField()
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    
    # Content
    description = models.TextField()
    file = models.FileField(upload_to='circulars/')
    
    # Metadata
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_circulars')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.circular_number} - {self.title}"


class Event(models.Model):
    """School events"""
    EVENT_TYPES = (
        ('academic', 'Academic'),
        ('sports', 'Sports'),
        ('cultural', 'Cultural'),
        ('holiday', 'Holiday'),
        ('meeting', 'Meeting'),
        ('exam', 'Exam'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    description = models.TextField()
    
    # Dates and Times
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    # Location
    venue = models.CharField(max_length=200)
    
    # Organizer
    organizer = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=15)
    contact_email = models.EmailField(blank=True)
    
    # Audience
    target_audience = models.CharField(max_length=200, help_text="Who should attend")
    
    # Media
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    attachment = models.FileField(upload_to='event_attachments/', blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_date', 'start_time']
    
    def __str__(self):
        return self.title
    
    def is_upcoming(self):
        return self.start_date >= timezone.now().date()
    
    def is_ongoing(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class Notification(models.Model):
    """User notifications"""
    NOTIFICATION_TYPES = (
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('danger', 'Alert'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='info')
    
    # Link (optional)
    link = models.CharField(max_length=200, blank=True, help_text="URL to redirect when clicked")
    
    # Status
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()


class SMSLog(models.Model):
    """SMS sending log"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    )
    
    recipient = models.CharField(max_length=15)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Response from SMS gateway
    provider_response = models.TextField(blank=True)
    provider_message_id = models.CharField(max_length=100, blank=True)
    
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_sms')
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"SMS to {self.recipient} - {self.status}"


class EmailLog(models.Model):
    """Email sending log"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('failed', 'Failed'),
    )
    
    recipient = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Response from email service
    provider_response = models.TextField(blank=True)
    provider_message_id = models.CharField(max_length=100, blank=True)
    
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_emails')
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Email to {self.recipient} - {self.status}"
