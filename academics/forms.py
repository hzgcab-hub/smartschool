from django import forms
from .models import (
    Exam, ExamSubject, ExamMark, ExamResult,
    GradeSystem, GradeRange, ReportCard
)
from classes.models import ClassSubject
from students.models import Student

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'exam_type', 'term', 'academic_year', 'class_group', 
                 'description', 'start_date', 'end_date', 'result_date', 'is_published']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'result_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        result_date = cleaned_data.get('result_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date")
        
        if result_date and end_date and result_date < end_date:
            raise forms.ValidationError("Result date should be after exam end date")
        
        return cleaned_data


class ExamSubjectForm(forms.ModelForm):
    class Meta:
        model = ExamSubject
        fields = ['exam', 'subject', 'exam_date', 'start_time', 'end_time', 
                 'max_marks', 'pass_marks', 'evaluator', 'room_number', 'is_completed']
        widgets = {
            'exam_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'exam' in self.data:
            try:
                exam_id = int(self.data.get('exam'))
                self.fields['subject'].queryset = ClassSubject.objects.filter(
                    class_group_id=Exam.objects.get(id=exam_id).class_group_id
                )
            except (ValueError, TypeError, Exam.DoesNotExist):
                pass
        elif self.instance.pk:
            self.fields['subject'].queryset = ClassSubject.objects.filter(
                class_group=self.instance.exam.class_group
            )


class MarksEntryForm(forms.Form):
    """Form for bulk marks entry"""
    def __init__(self, *args, **kwargs):
        students = kwargs.pop('students', [])
        exam_subject = kwargs.pop('exam_subject', None)
        super().__init__(*args, **kwargs)
        
        for student in students:
            prefix = f"student_{student.id}"
            self.fields[f"{prefix}_theory"] = forms.FloatField(
                required=False,
                min_value=0,
                max_value=exam_subject.max_marks if exam_subject else 100,
                label=f"{student.user.get_full_name()} - Theory",
                widget=forms.NumberInput(attrs={'class': 'form-control theory-marks', 'step': '0.5'})
            )
            self.fields[f"{prefix}_practical"] = forms.FloatField(
                required=False,
                min_value=0,
                max_value=exam_subject.subject.subject.practical_marks if exam_subject and exam_subject.subject.subject.practical_marks > 0 else 0,
                label=f"{student.user.get_full_name()} - Practical",
                widget=forms.NumberInput(attrs={'class': 'form-control practical-marks', 'step': '0.5'})
            )
            self.fields[f"{prefix}_absent"] = forms.BooleanField(
                required=False,
                label=f"{student.user.get_full_name()} - Absent",
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
            )
            self.fields[f"{prefix}_malpractice"] = forms.BooleanField(
                required=False,
                label=f"{student.user.get_full_name()} - Malpractice",
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
            )
            self.fields[f"{prefix}_remarks"] = forms.CharField(
                required=False,
                label=f"{student.user.get_full_name()} - Remarks",
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )


class SingleMarkEntryForm(forms.ModelForm):
    class Meta:
        model = ExamMark
        fields = ['theory_marks', 'practical_marks', 'is_absent', 'is_malpractice', 'grace_marks', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.exam_subject:
            max_theory = self.instance.exam_subject.subject.subject.theory_marks
            max_practical = self.instance.exam_subject.subject.subject.practical_marks
            
            self.fields['theory_marks'].widget.attrs['max'] = max_theory
            self.fields['practical_marks'].widget.attrs['max'] = max_practical


class GradeSystemForm(forms.ModelForm):
    class Meta:
        model = GradeSystem
        fields = ['name', 'academic_year', 'is_active']


class GradeRangeForm(forms.ModelForm):
    class Meta:
        model = GradeRange
        fields = ['grade', 'min_percentage', 'max_percentage', 'grade_point', 'description']
        widgets = {
            'min_percentage': forms.NumberInput(attrs={'step': '0.1'}),
            'max_percentage': forms.NumberInput(attrs={'step': '0.1'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        min_percentage = cleaned_data.get('min_percentage')
        max_percentage = cleaned_data.get('max_percentage')
        
        if min_percentage and max_percentage and min_percentage >= max_percentage:
            raise forms.ValidationError("Max percentage must be greater than min percentage")
        
        return cleaned_data


class ResultPublishForm(forms.Form):
    publish = forms.BooleanField(required=False, label="Publish Results")
    notify_students = forms.BooleanField(required=False, label="Notify students via email")
    notify_parents = forms.BooleanField(required=False, label="Notify parents via SMS")