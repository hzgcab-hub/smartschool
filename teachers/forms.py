from django import forms
from django.contrib.auth import get_user_model
from .models import Teacher, TeacherAttendance, TeacherLeave, TeacherQualification, TeacherSubject
from datetime import date

User = get_user_model()

class TeacherRegistrationForm(forms.ModelForm):
    """Form for registering a new teacher with user account"""
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    
    class Meta:
        model = Teacher
        fields = [
            'employee_id', 'joining_date', 'qualification', 'qualification_level',
            'specialization', 'experience_years', 'employment_type',
            'gender', 'blood_group', 'emergency_contact', 'emergency_contact_name',
            'bank_name', 'bank_account_no', 'ifsc_code', 'pan_card',
            'salary', 'subjects'
        ]
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match')
        
        return cleaned_data
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists')
        return username
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id']
        if Teacher.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError('Employee ID already exists')
        return employee_id
    
    def save(self, commit=True):
        # Create user first
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            role='teacher'
        )
        
        # Create teacher profile
        teacher = super().save(commit=False)
        teacher.user = user
        
        if commit:
            teacher.save()
        
        return teacher


class TeacherEditForm(forms.ModelForm):
    """Form for editing teacher details"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    
    class Meta:
        model = Teacher
        fields = [
            'employee_id', 'joining_date', 'qualification', 'qualification_level',
            'specialization', 'experience_years', 'employment_type',
            'is_class_teacher', 'assigned_class', 'assigned_section',
            'gender', 'blood_group', 'emergency_contact', 'emergency_contact_name',
            'bank_name', 'bank_account_no', 'ifsc_code', 'pan_card',
            'salary', 'subjects', 'is_active'
        ]
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
    
    def save(self, commit=True):
        teacher = super().save(commit=False)
        
        # Update user details
        user = teacher.user
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            teacher.save()
        
        return teacher


class TeacherAttendanceForm(forms.ModelForm):
    class Meta:
        model = TeacherAttendance
        fields = ['teacher', 'status', 'check_in_time', 'check_out_time', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'check_in_time': forms.TimeInput(attrs={'type': 'time'}),
            'check_out_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class TeacherLeaveForm(forms.ModelForm):
    class Meta:
        model = TeacherLeave
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date cannot be before start date")
        
        return cleaned_data


class TeacherQualificationForm(forms.ModelForm):
    class Meta:
        model = TeacherQualification
        fields = ['degree', 'institution', 'year_passed', 'percentage', 'division', 'certificate']
        widgets = {
            'year_passed': forms.NumberInput(attrs={'min': 1950, 'max': date.today().year}),
        }