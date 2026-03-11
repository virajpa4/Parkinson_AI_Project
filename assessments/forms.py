from django import forms
from .models import SymptomQuiz, SpiralDrawing, VoiceRecording, MRIScan, PostureVideo
from django.core.validators import FileExtensionValidator

class SymptomQuizForm(forms.ModelForm):
    class Meta:
        model = SymptomQuiz
        fields = [
            'tremor', 'bradykinesia', 'rigidity', 'postural_instability',
            'sleep_problems', 'depression', 'anxiety', 'cognitive_changes',
            'daily_activities', 'symptom_duration', 'additional_notes'
        ]
        widgets = {
            'tremor': forms.RadioSelect(choices=[(i, str(i)) for i in range(5)]),
            'bradykinesia': forms.RadioSelect(choices=[(i, str(i)) for i in range(5)]),
            'rigidity': forms.RadioSelect(choices=[(i, str(i)) for i in range(5)]),
            'postural_instability': forms.RadioSelect(choices=[(i, str(i)) for i in range(5)]),
            'daily_activities': forms.RadioSelect(choices=[(i, str(i)) for i in range(5)]),
            'additional_notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Any other symptoms or concerns...'}),
        }

class SpiralDrawingForm(forms.Form):
    drawing_image = forms.ImageField(
        label='Upload Spiral Drawing',
        help_text='Upload an image of your spiral drawing',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    
    # Alternative: Canvas drawing (will be handled via JavaScript)
    drawing_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

class VoiceRecordingForm(forms.ModelForm):
    class Meta:
        model = VoiceRecording
        fields = ['audio_file']
        widgets = {
            'audio_file': forms.FileInput(attrs={
                'accept': 'audio/*',
                'class': 'form-control'
            })
        }

class MRIScanForm(forms.ModelForm):
    class Meta:
        model = MRIScan
        fields = ['scan_image']
        widgets = {
            'scan_image': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control'
            })
        }

class PostureVideoForm(forms.ModelForm):
    class Meta:
        model = PostureVideo
        fields = ['video_file']
        widgets = {
            'video_file': forms.FileInput(attrs={
                'accept': 'video/*',
                'class': 'form-control'
            })
        }

class AssessmentSelectionForm(forms.Form):
    ASSESSMENT_CHOICES = [
        ('spiral', 'Spiral Drawing Test'),
        ('voice', 'Voice Recording Test'),
        ('quiz', 'Symptom Questionnaire'),
        ('video', 'Posture & Gait Video Analysis'),
        ('mri', 'MRI Scan Analysis (If available)'),
    ]
    
    assessment_type = forms.ChoiceField(
        choices=ASSESSMENT_CHOICES,
        widget=forms.RadioSelect,
        label='Select Assessment Type'
    )