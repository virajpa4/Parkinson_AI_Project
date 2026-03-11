from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    # Assessment selection
    path('', views.assessment_selection, name='assessment_selection'),
    
    # Individual assessments
    path('quiz/', views.symptom_quiz, name='symptom_quiz'),
    path('spiral/', views.spiral_drawing_assessment, name='spiral_drawing'),
    path('voice/', views.voice_recording_assessment, name='voice_recording'),
    path('mri/', views.mri_scan_assessment, name='mri_scan'),
    path('video/', views.posture_video_assessment, name='posture_video'),
    
    # Results
    path('result/<int:assessment_id>/', views.assessment_result, name='assessment_result'),
    path('quiz/result/<int:assessment_id>/', views.assessment_result, {'assessment_type': 'quiz'}, name='quiz_result'),
    path('spiral/result/<int:assessment_id>/', views.assessment_result, {'assessment_type': 'spiral'}, name='spiral_result'),
    path('voice/result/<int:assessment_id>/', views.assessment_result, name='voice_result'),
    path('mri/result/<int:assessment_id>/', views.assessment_result, name='mri_result'),
    path('video/result/<int:assessment_id>/', views.assessment_result, name='video_result'),
    
    # History
     path('history/', views.assessment_result, name='history'),
    
    # API endpoints
   # path('api/save-drawing/', views.api_save_drawing, name='api_save_drawing'),


    # Simple test URLs
    path('', views.simple_assessment, name='assessment_selection'),
    path('spiral/', views.spiral_test, name='spiral_drawing'),
    path('voice/', views.voice_test, name='voice_recording'),
    path('quiz/', views.quiz_test, name='symptom_quiz'),
]
