from django.contrib import admin
from .models import (
    PatientDashboard, ProgressChart, DoctorPatientMapping,
    Alert, ProgressGoal, TreatmentPlan
)

@admin.register(PatientDashboard)
class PatientDashboardAdmin(admin.ModelAdmin):
    list_display = ['user', 'overall_risk_score', 'total_assessments', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['user__username', 'user__email']

@admin.register(DoctorPatientMapping)
class DoctorPatientMappingAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'patient', 'assigned_date', 'is_active']
    list_filter = ['is_active', 'assigned_date']
    search_fields = ['doctor__username', 'patient__username']

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'alert_type', 'priority', 'is_read', 'created_at']
    list_filter = ['alert_type', 'priority', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']

@admin.register(ProgressGoal)
class ProgressGoalAdmin(admin.ModelAdmin):
    list_display = ['patient', 'title', 'current_value', 'target_value', 'is_completed']
    list_filter = ['is_completed', 'created_at']
    search_fields = ['patient__username', 'title']

@admin.register(TreatmentPlan)
class TreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'title', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['patient__username', 'doctor__username', 'title']

@admin.register(ProgressChart)
class ProgressChartAdmin(admin.ModelAdmin):
    list_display = ['dashboard', 'title', 'chart_type', 'is_active', 'order']
    list_filter = ['chart_type', 'is_active']
    search_fields = ['dashboard__user__username', 'title']