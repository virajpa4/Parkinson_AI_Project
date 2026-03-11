import os
import numpy as np
import pandas as pd
import joblib
import json
from django.conf import settings
from django.db import models
from assessments.models import Assessment

class AIModel(models.Model):
    MODEL_TYPES = [
        ('spiral', 'Spiral Drawing Model'),
        ('voice', 'Voice Analysis Model'),
        ('mri', 'MRI Scan Model'),
        ('quiz', 'Quiz Scoring Model'),
        ('ensemble', 'Ensemble Model'),
    ]
    
    MODEL_STATUS = [
        ('trained', 'Trained'),
        ('training', 'Training'),
        ('untrained', 'Untrained'),
        ('failed', 'Training Failed'),
    ]
    
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    version = models.CharField(max_length=20, default='1.0.0')
    description = models.TextField(blank=True)
    accuracy = models.FloatField(default=0.0)
    precision = models.FloatField(default=0.0)
    recall = models.FloatField(default=0.0)
    f1_score = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=MODEL_STATUS, default='untrained')
    model_file = models.FileField(upload_to='ai_models/', blank=True, null=True)
    scaler_file = models.FileField(upload_to='ai_scalers/', blank=True, null=True)
    feature_columns = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.model_type}) - v{self.version}"
    
    def get_model_path(self):
        """Get full path to model file"""
        if self.model_file:
            return os.path.join(settings.MEDIA_ROOT, self.model_file.name)
        return None
    
    def get_scaler_path(self):
        """Get full path to scaler file"""
        if self.scaler_file:
            return os.path.join(settings.MEDIA_ROOT, self.scaler_file.name)
        return None

class ModelTrainingLog(models.Model):
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='training_logs')
    dataset_size = models.IntegerField()
    training_duration = models.FloatField(help_text="Duration in seconds")
    training_date = models.DateTimeField(auto_now_add=True)
    metrics = models.JSONField(default=dict)
    training_log = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('running', 'Running'),
    ])
    
    class Meta:
        ordering = ['-training_date']
    
    def __str__(self):
        return f"{self.model.name} - {self.training_date}"

class PredictionResult(models.Model):
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE, related_name='ai_prediction')
    model_used = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    prediction = models.BooleanField(default=False)
    confidence = models.FloatField(default=0.0)
    probabilities = models.JSONField(default=dict)
    features_used = models.JSONField(default=list)
    prediction_time = models.FloatField(help_text="Prediction time in seconds")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prediction for {self.assessment.user.username} - {self.prediction} ({self.confidence:.2%})"