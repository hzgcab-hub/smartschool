from django import forms
from .models import Notice, Circular, Event, NoticeCategory
from classes.models import Class
from students.models import Student
from teachers.models import Teacher
from django.utils import timezone

class NoticeCategoryForm(forms.ModelForm):
    class Meta:
        model = NoticeCategory
        fields = ['name', 'description', 'color', 'icon']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = [
            'title', 'content', 'category', 'priority', 'status',
            'publish_date', 'expiry_date', 'audience_type',
            'target_classes', 'target_students', 'target_teachers',
            'attachment', 'image', 'is_pinned', 'requires_acknowledgment',
            'send_email', 'send_sms', 'send_push'
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 8}),
            'publish_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'target_classes': forms.SelectMultiple(attrs={'class': 'select2'}),
            'target_students': forms.SelectMultiple(attrs={'class': 'select2'}),
            'target_teachers': forms.SelectMultiple(attrs={'class': 'select2'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['publish_date'].initial = timezone.now().date()
        self.fields['target_classes'].queryset = Class.objects.filter(is_active=True)
        self.fields['target_students'].queryset = Student.objects.filter(is_active=True)
        self.fields['target_teachers'].queryset = Teacher.objects.filter(is_active=True)
        
        # Make some fields optional based on audience_type
        self.fields['target_classes'].required = False
        self.fields['target_students'].required = False
        self.fields['target_teachers'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        audience_type = cleaned_data.get('audience_type')
        target_classes = cleaned_data.get('target_classes')
        target_students = cleaned_data.get('target_students')
        target_teachers = cleaned_data.get('target_teachers')
        
        if audience_type == 'specific':
            if not target_classes and not target_students and not target_teachers:
                raise forms.ValidationError("Please select at least one target audience.")
        
        return cleaned_data


class CircularForm(forms.ModelForm):
    class Meta:
        model = Circular
        fields = [
            'title', 'circular_number', 'circular_type',
            'issue_date', 'effective_from', 'effective_to',
            'description', 'file', 'is_active'
        ]
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'effective_from': forms.DateInput(attrs={'type': 'date'}),
            'effective_to': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['issue_date'].initial = timezone.now().date()
        self.fields['effective_from'].initial = timezone.now().date()


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'event_type', 'description',
            'start_date', 'end_date', 'start_time', 'end_time',
            'venue', 'organizer', 'contact_person', 'contact_phone', 'contact_email',
            'target_audience', 'image', 'attachment', 'is_featured'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date.")
        
        if start_date == end_date and start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time.")
        
        return cleaned_data


class NoticeSearchForm(forms.Form):
    query = forms.CharField(max_length=100, required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Search notices...', 'class': 'form-control'}
    ))
    category = forms.ModelChoiceField(
        queryset=NoticeCategory.objects.all(),
        required=False,
        empty_label="All Categories"
    )
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + list(Notice.PRIORITY_CHOICES),
        required=False
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )


class BulkNotificationForm(forms.Form):
    """Form for sending bulk notifications"""
    RECIPIENT_CHOICES = [
        ('all_students', 'All Students'),
        ('all_teachers', 'All Teachers'),
        ('all_parents', 'All Parents'),
        ('all_staff', 'All Staff'),
        ('specific_class', 'Specific Class'),
        ('specific_students', 'Specific Students'),
    ]
    
    recipient_type = forms.ChoiceField(choices=RECIPIENT_CHOICES, widget=forms.RadioSelect)
    target_class = forms.ModelChoiceField(
        queryset=Class.objects.filter(is_active=True),
        required=False,
        empty_label="Select Class"
    )
    target_students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2'})
    )
    
    title = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))
    
    send_email = forms.BooleanField(required=False, initial=True)
    send_sms = forms.BooleanField(required=False)
    send_push = forms.BooleanField(required=False, initial=True)
    
    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        target_class = cleaned_data.get('target_class')
        target_students = cleaned_data.get('target_students')
        
        if recipient_type == 'specific_class' and not target_class:
            raise forms.ValidationError("Please select a class.")
        
        if recipient_type == 'specific_students' and not target_students:
            raise forms.ValidationError("Please select at least one student.")
        
        return cleaned_data