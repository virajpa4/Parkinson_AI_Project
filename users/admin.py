from django.contrib import admin
from .models import UserProfile, MedicalHistory

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'phone', 'gender']
    list_filter = ['user_type', 'gender']
    search_fields = ['user__username', 'user__email', 'phone']

@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'condition', 'diagnosis_date']
    list_filter = ['condition', 'diagnosis_date']
    search_fields = ['patient__username', 'condition', 'symptoms']