from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    
    # Main dashboard
    path('', views.dashboard_home, name='dashboard_home'),
    path('patient/', views.patient_dashboard, name='patient_dashboard'),
    path('doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    
    # Patient management
    path('patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    
    # Progress tracking
    path('progress/', views.progress_charts, name='progress_charts'),
    path('add-goal/', views.add_progress_goal, name='add_goal'),
    path('update-goal/<int:goal_id>/', views.update_goal_progress, name='update_goal'),
    
    # Alerts
    path('alert/read/<int:alert_id>/', views.mark_alert_read, name='mark_alert_read'),
    path('send-alert/<int:patient_id>/', views.send_alert, name='send_alert'),
    
    # API endpoints
    path('api/progress-data/', views.api_progress_data, name='api_progress_data'),
]