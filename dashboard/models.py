from django.db import models
from django.contrib.auth.models import User
from assessments.models import Assessment, PatientHistory
from django.core.validators import MinValueValidator, MaxValueValidator

class PatientDashboard(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_dashboard')
    overall_risk_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    last_assessment_date = models.DateTimeField(null=True, blank=True)
    total_assessments = models.IntegerField(default=0)
    improvement_rate = models.FloatField(default=0)  # Percentage improvement
    monitored_since = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Patient Dashboard"
        verbose_name_plural = "Patient Dashboards"
    
    def __str__(self):
        return f"Dashboard - {self.user.username}"
    
    def update_dashboard(self):
        """Update dashboard metrics from assessment history"""
        assessments = Assessment.objects.filter(user=self.user)
        self.total_assessments = assessments.count()
        
        if assessments.exists():
            self.last_assessment_date = assessments.latest('date_taken').date_taken
            
            # Calculate average risk score from recent assessments
            recent_assessments = assessments.order_by('-date_taken')[:5]
            if recent_assessments:
                avg_score = sum([a.severity_score for a in recent_assessments]) / len(recent_assessments)
                self.overall_risk_score = min(avg_score, 100)
        
        self.save()

class ProgressChart(models.Model):
    CHART_TYPES = [
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('radar', 'Radar Chart'),
        ('gauge', 'Gauge Chart'),
    ]
    
    dashboard = models.ForeignKey(PatientDashboard, on_delete=models.CASCADE, related_name='charts')
    chart_type = models.CharField(max_length=10, choices=CHART_TYPES, default='line')
    title = models.CharField(max_length=100)
    data_config = models.JSONField(default=dict)  # Chart configuration
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.title} - {self.dashboard.user.username}"

class DoctorPatientMapping(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patients')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctors')
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['doctor', 'patient']
        verbose_name = "Doctor-Patient Mapping"
        verbose_name_plural = "Doctor-Patient Mappings"
    
    def __str__(self):
        return f"Dr. {self.doctor.username} -> {self.patient.username}"

class Alert(models.Model):
    ALERT_TYPES = [
        ('high_risk', 'High Risk Detected'),
        ('new_assessment', 'New Assessment Completed'),
        ('symptom_worsening', 'Symptom Worsening Detected'),
        ('reminder', 'Assessment Reminder'),
        ('system', 'System Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    assessment = models.ForeignKey(Assessment, on_delete=models.SET_NULL, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.user.username}"

class ProgressGoal(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_value = models.FloatField()
    current_value = models.FloatField(default=0)
    unit = models.CharField(max_length=20, default='points')
    start_date = models.DateField()
    target_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.patient.username}"
    
    def progress_percentage(self):
        if self.target_value == 0:
            return 0
        progress = (self.current_value / self.target_value) * 100
        return min(progress, 100)

class TreatmentPlan(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='treatment_plans')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescribed_plans')
    title = models.CharField(max_length=200)
    description = models.TextField()
    medications = models.TextField(blank=True)
    exercises = models.TextField(blank=True)
    diet_recommendations = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.patient.username}"