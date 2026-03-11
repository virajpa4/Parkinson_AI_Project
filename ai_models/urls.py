from django.urls import path
from . import views

app_name = 'ai_models'

urlpatterns = [
    # Dashboard
    path('', views.model_dashboard, name='model_dashboard'),
    path('train/', views.train_models, name='train_models'),
    path('model/<int:model_id>/', views.model_details, name='model_details'),
    
    # Prediction endpoints
    path('predict/spiral/', views.predict_spiral, name='predict_spiral'),
    path('predict/voice/', views.predict_voice, name='predict_voice'),
    path('predict/quiz/', views.predict_quiz, name='predict_quiz'),
    path('predict/ensemble/', views.ensemble_predict, name='ensemble_predict'),
    path('inference/', views.run_inference, name='run_inference'),
    
    # API endpoints
    path('api/status/', views.api_model_status, name='api_model_status'),
]