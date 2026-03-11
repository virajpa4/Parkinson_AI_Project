from django import forms
from .models import ProgressGoal, TreatmentPlan, Alert
from django.contrib.auth.models import User

class ProgressGoalForm(forms.ModelForm):
    class Meta:
        model = ProgressGoal
        fields = ['title', 'description', 'target_value', 'unit', 'target_date']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class TreatmentPlanForm(forms.ModelForm):
    class Meta:
        model = TreatmentPlan
        fields = ['title', 'description', 'medications', 'exercises', 'diet_recommendations', 'follow_up_date']
        widgets = {
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'medications': forms.Textarea(attrs={'rows': 3}),
            'exercises': forms.Textarea(attrs={'rows': 3}),
            'diet_recommendations': forms.Textarea(attrs={'rows': 3}),
        }

class PatientSelectionForm(forms.Form):
    patient = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Select Patient",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, doctor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only patients assigned to this doctor
        from .models import DoctorPatientMapping
        patient_ids = DoctorPatientMapping.objects.filter(
            doctor=doctor, 
            is_active=True
        ).values_list('patient_id', flat=True)
        self.fields['patient'].queryset = User.objects.filter(id__in=patient_ids)

class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ['title', 'message', 'priority']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }