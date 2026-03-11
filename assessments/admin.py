from django.contrib import admin
from .models import (
    Assessment, SpiralDrawing, VoiceRecording, 
    SymptomQuiz, MRIScan, PostureVideo, PatientHistory
)

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'assessment_type', 'date_taken', 'parkinson_prediction', 'parkinson_stage', 'confidence_score']
    list_filter = ['assessment_type', 'parkinson_prediction', 'date_taken']
    search_fields = ['user__username', 'notes']

@admin.register(SpiralDrawing)
class SpiralDrawingAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'smoothness_score', 'tremor_frequency', 'amplitude_variation']

@admin.register(VoiceRecording)
class VoiceRecordingAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'duration', 'jitter', 'shimmer', 'hnr']

@admin.register(SymptomQuiz)
class SymptomQuizAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'tremor', 'bradykinesia', 'rigidity', 'calculate_score']

@admin.register(MRIScan)
class MRIScanAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'nigra_volume', 'asymmetry_index', 'cnn_confidence']

@admin.register(PostureVideo)
class PostureVideoAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'gait_speed', 'arm_swing', 'balance_score']

@admin.register(PatientHistory)
class PatientHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'assessment_date', 'overall_severity', 'prediction']
    list_filter = ['prediction', 'assessment_date']