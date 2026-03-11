from django import forms
from .models import Class, Section, Subject, ClassSubject, Timetable, Homework, HomeworkSubmission
from teachers.models import Teacher
from students.models import Student

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'numeric_value', 'academic_year', 'class_teacher', 'room_number', 'capacity', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['class_teacher'].queryset = Teacher.objects.filter(is_active=True)
        self.fields['class_teacher'].required = False


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'class_group', 'class_teacher', 'room_number', 'capacity', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['class_teacher'].queryset = Teacher.objects.filter(is_active=True)
        self.fields['class_teacher'].required = False


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description', 'is_language', 'is_practical', 
                 'theory_marks', 'practical_marks', 'pass_marks', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ClassSubjectForm(forms.ModelForm):
    class Meta:
        model = ClassSubject
        fields = ['class_group', 'section', 'subject', 'teacher', 'is_mandatory', 'max_students']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = Teacher.objects.filter(is_active=True)
        self.fields['section'].required = False


class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ['class_group', 'section', 'day', 'start_time', 'end_time', 'subject', 'teacher', 'room_number']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = Teacher.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time")
        
        return cleaned_data


class HomeworkForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ['class_group', 'section', 'subject', 'title', 'description', 'due_date', 'attachment']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['section'].required = False


class HomeworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ['submission_file']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['submission_file'].required = True


class HomeworkGradingForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ['marks_obtained', 'feedback']