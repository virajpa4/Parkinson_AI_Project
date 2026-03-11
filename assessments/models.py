from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ('spiral', 'Spiral Drawing'),
        ('voice', 'Voice Recording'),
        ('mri', 'MRI Scan'),
        ('quiz', 'Symptom Quiz'),
        ('video', 'Posture Video'),
    ]
    
    PARKINSON_STAGES = [
        (0, 'No Parkinson\'s'),
        (1, 'Stage 1 - Unilateral symptoms'),
        (2, 'Stage 2 - Bilateral symptoms, balance intact'),
        (3, 'Stage 3 - Balance impairment'),
        (4, 'Stage 4 - Severe disability'),
        (5, 'Stage 5 - Wheelchair bound or bedridden'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assessment_type = models.CharField(max_length=10, choices=ASSESSMENT_TYPES)
    date_taken = models.DateTimeField(auto_now_add=True)
    parkinson_prediction = models.BooleanField(default=False)
    parkinson_stage = models.IntegerField(choices=PARKINSON_STAGES, null=True, blank=True)
    confidence_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    severity_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-date_taken']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_assessment_type_display()} - {self.date_taken}"

class SpiralDrawing(models.Model):
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE, related_name='spiral_drawing')
    drawing_image = models.ImageField(upload_to='spiral_drawings/')
    drawing_data = models.JSONField(blank=True, null=True)  # Store drawing coordinates
    smoothness_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    tremor_frequency = models.FloatField(null=True, blank=True)  # Hz
    amplitude_variation = models.FloatField(null=True, blank=True)  # mm
    symmetry_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # seconds
    ai_analysis = models.JSONField(blank=True, null=True)  # Store AI model results
    
    def __str__(self):
        return f"Spiral Drawing - {self.assessment.user.username}"

class VoiceRecording(models.Model):
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE, related_name='voice_recording')
    audio_file = models.FileField(upload_to='voice_recordings/')
    duration = models.FloatField(null=True, blank=True)  # seconds
    pitch_variation = models.FloatField(null=True, blank=True)
    jitter = models.FloatField(null=True, blank=True)  # Measure of frequency instability
    shimmer = models.FloatField(null=True, blank=True)  # Measure of amplitude instability
    hnr = models.FloatField(null=True, blank=True)  # Harmonics-to-noise ratio
    mfcc_features = models.JSONField(blank=True, null=True)  # Mel-frequency cepstral coefficients
    speech_rate = models.FloatField(null=True, blank=True)  # words per second
    articulation_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    
    def __str__(self):
        return f"Voice Recording - {self.assessment.user.username}"

class MRIScan(models.Model):
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE, related_name='mri_scan')
    scan_image = models.ImageField(upload_to='mri_scans/')
    scan_type = models.CharField(max_length=50, default='T1-weighted')
    nigra_volume = models.FloatField(null=True, blank=True)  # Substantia nigra volume
    caudate_volume = models.FloatField(null=True, blank=True)  # Caudate nucleus volume
    putamen_volume = models.FloatField(null=True, blank=True)  # Putamen volume
    asymmetry_index = models.FloatField(null=True, blank=True)
    cnn_confidence = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    detected_abnormalities = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return f"MRI Scan - {self.assessment.user.username}"

class SymptomQuiz(models.Model):
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE, related_name='symptom_quiz')
    
    # Motor Symptoms (0-4 scale: 0=None, 1=Slight, 2=Mild, 3=Moderate, 4=Severe)
    tremor = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], default=0)
    bradykinesia = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], default=0)
    rigidity = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], default=0)
    postural_instability = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)], default=0)
    
    # Non-Motor Symptoms
    sleep_problems = models.BooleanField(default=False)
    depression = models.BooleanField(default=False)
    anxiety = models.BooleanField(default=False)
    cognitive_changes = models.BooleanField(default=False)
    
    # Functional Impact
    daily_activities = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)], 
        default=0,
        help_text="0=Normal, 4=Severe difficulty"
    )
    
    # Duration
    symptom_duration = models.IntegerField(
        choices=[(1, '<6 months'), (2, '6-12 months'), (3, '1-2 years'), (4, '>2 years')],
        default=1
    )
    
    # Additional notes
    additional_notes = models.TextField(blank=True)
    
    def calculate_score(self):
        """Calculate total symptom score"""
        motor_score = self.tremor + self.bradykinesia + self.rigidity + self.postural_instability
        non_motor_score = sum([self.sleep_problems, self.depression, self.anxiety, self.cognitive_changes]) * 2
        functional_score = self.daily_activities * 2
        duration_multiplier = self.symptom_duration * 0.5
        
        total_score = (motor_score + non_motor_score + functional_score) * duration_multiplier
        return min(total_score, 100)  # Cap at 100
    
    def __str__(self):
        return f"Symptom Quiz - {self.assessment.user.username}"

class PostureVideo(models.Model):
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE, related_name='posture_video')
    video_file = models.FileField(upload_to='posture_videos/')
    duration = models.FloatField(null=True, blank=True)
    
    # Gait analysis
    stride_length = models.FloatField(null=True, blank=True)
    gait_speed = models.FloatField(null=True, blank=True)
    step_width = models.FloatField(null=True, blank=True)
    arm_swing = models.FloatField(null=True, blank=True)  # Arm swing amplitude
    
    # Posture analysis
    posture_stability = models.FloatField(null=True, blank=True)
    trunk_flexion = models.FloatField(null=True, blank=True)
    balance_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    
    # Movement features
    movement_features = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return f"Posture Video - {self.assessment.user.username}"

class PatientHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_history')
    assessment_date = models.DateTimeField(auto_now_add=True)
    overall_severity = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    spiral_score = models.FloatField(null=True, blank=True)
    voice_score = models.FloatField(null=True, blank=True)
    mri_score = models.FloatField(null=True, blank=True)
    quiz_score = models.FloatField(null=True, blank=True)
    posture_score = models.FloatField(null=True, blank=True)
    prediction = models.CharField(max_length=50, default='Pending')
    recommendation = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-assessment_date']
        verbose_name_plural = "Patient Histories"
    
    def __str__(self):
        return f"{self.user.username} - {self.assessment_date}"