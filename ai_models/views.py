from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
import json
import os
from django.conf import settings

from .models import AIModel, ModelTrainingLog, PredictionResult
from assessments.models import Assessment
from .ml_utils import ParkinsonPredictor, SpiralDrawingProcessor, VoiceProcessor, SymptomQuizProcessor
from .train_models import ModelTrainer

# Global predictor instance
_predictor = None

def get_predictor():
    """Get or create predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = ParkinsonPredictor()
    return _predictor

@login_required
def model_dashboard(request):
    """AI Model dashboard"""
    models = AIModel.objects.filter(is_active=True)
    training_logs = ModelTrainingLog.objects.all()[:10]
    
    context = {
        'models': models,
        'training_logs': training_logs,
        'total_models': models.count(),
        'trained_models': models.filter(status='trained').count(),
    }
    
    return render(request, 'ai_models/dashboard.html', context)

@login_required
def train_models(request):
    """Train AI models"""
    if request.method == 'POST':
        try:
            trainer = ModelTrainer()
            results = trainer.train_all_models()
            
            # Update model records
            for model_type, result in results.items():
                if result:
                    model, created = AIModel.objects.update_or_create(
                        model_type=model_type,
                        defaults={
                            'name': f'Parkinson {model_type.title()} Model',
                            'version': '1.0.0',
                            'accuracy': result['metrics']['accuracy'],
                            'precision': result['metrics']['precision'],
                            'recall': result['metrics']['recall'],
                            'f1_score': result['metrics']['f1_score'],
                            'status': 'trained',
                            'is_active': True,
                        }
                    )
                    
                    # Create training log
                    ModelTrainingLog.objects.create(
                        model=model,
                        dataset_size=100,  # Simulated
                        training_duration=30.5,  # Simulated
                        metrics=result['metrics'],
                        training_log='Training completed successfully',
                        status='success'
                    )
            
            messages.success(request, 'AI models trained successfully!')
            return redirect('ai_models:model_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error training models: {str(e)}')
            return redirect('ai_models:model_dashboard')
    
    return render(request, 'ai_models/train_models.html')

@login_required
def predict_spiral(request):
    """Make prediction from spiral drawing"""
    if request.method == 'POST':
        try:
            drawing_file = request.FILES.get('drawing_image')
            if not drawing_file:
                return JsonResponse({'error': 'No drawing file provided'}, status=400)
            
            # Process drawing
            processor = SpiralDrawingProcessor()
            features = processor.preprocess_image(drawing_file)
            
            if features is None:
                return JsonResponse({'error': 'Could not process drawing'}, status=400)
            
            # Get prediction
            predictor = get_predictor()
            prediction = predictor.predict_spiral(features)
            
            # Create assessment record
            assessment = Assessment.objects.create(
                user=request.user,
                assessment_type='spiral',
                parkinson_prediction=prediction['prediction'],
                confidence_score=prediction['confidence'] * 100,
                severity_score=prediction['confidence'] * 100,
            )
            
            # Save prediction result
            PredictionResult.objects.create(
                assessment=assessment,
                prediction=prediction['prediction'],
                confidence=prediction['confidence'],
                probabilities=prediction['probabilities'],
                features_used=list(features.keys()),
                prediction_time=0.5,
            )
            
            return JsonResponse({
                'success': True,
                'prediction': prediction['prediction'],
                'confidence': prediction['confidence'],
                'assessment_id': assessment.id,
                'features': features,
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def predict_voice(request):
    """Make prediction from voice recording"""
    if request.method == 'POST':
        try:
            audio_file = request.FILES.get('audio_file')
            if not audio_file:
                return JsonResponse({'error': 'No audio file provided'}, status=400)
            
            # Process audio
            processor = VoiceProcessor()
            features = processor.extract_features(audio_file)
            
            if features is None:
                return JsonResponse({'error': 'Could not process audio'}, status=400)
            
            # Get prediction
            predictor = get_predictor()
            prediction = predictor.predict_voice(features)
            
            # Create assessment record
            assessment = Assessment.objects.create(
                user=request.user,
                assessment_type='voice',
                parkinson_prediction=prediction['prediction'],
                confidence_score=prediction['confidence'] * 100,
                severity_score=prediction['confidence'] * 100,
            )
            
            # Save prediction result
            PredictionResult.objects.create(
                assessment=assessment,
                prediction=prediction['prediction'],
                confidence=prediction['confidence'],
                probabilities=prediction['probabilities'],
                features_used=list(features.keys()),
                prediction_time=0.5,
            )
            
            return JsonResponse({
                'success': True,
                'prediction': prediction['prediction'],
                'confidence': prediction['confidence'],
                'assessment_id': assessment.id,
                'features': features,
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def predict_quiz(request):
    """Make prediction from symptom quiz"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Process quiz data
            processor = SymptomQuizProcessor()
            features = processor.calculate_features(data)
            
            # Get prediction
            predictor = get_predictor()
            prediction = predictor.predict_quiz(features)
            
            # Create assessment record
            assessment = Assessment.objects.create(
                user=request.user,
                assessment_type='quiz',
                parkinson_prediction=prediction['prediction'],
                confidence_score=prediction['confidence'] * 100,
                severity_score=features['total_score'],
            )
            
            # Save prediction result
            PredictionResult.objects.create(
                assessment=assessment,
                prediction=prediction['prediction'],
                confidence=prediction['confidence'],
                probabilities=prediction['probabilities'],
                features_used=list(features.keys()),
                prediction_time=0.1,
            )
            
            return JsonResponse({
                'success': True,
                'prediction': prediction['prediction'],
                'confidence': prediction['confidence'],
                'assessment_id': assessment.id,
                'features': features,
                'total_score': features['total_score'],
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def ensemble_predict(request):
    """Make ensemble prediction from multiple assessments"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            assessment_ids = data.get('assessment_ids', [])
            
            if not assessment_ids:
                return JsonResponse({'error': 'No assessment IDs provided'}, status=400)
            
            # Get predictions for each assessment
            predictions = []
            for assessment_id in assessment_ids:
                try:
                    prediction_result = PredictionResult.objects.get(assessment_id=assessment_id)
                    predictions.append({
                        'prediction': prediction_result.prediction,
                        'confidence': prediction_result.confidence,
                        'type': prediction_result.assessment.assessment_type,
                    })
                except PredictionResult.DoesNotExist:
                    continue
            
            # Get ensemble prediction
            predictor = get_predictor()
            ensemble_prediction = predictor.ensemble_predict(predictions)
            
            return JsonResponse({
                'success': True,
                'prediction': ensemble_prediction['prediction'],
                'confidence': ensemble_prediction['confidence'],
                'component_predictions': predictions,
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def model_details(request, model_id):
    """View model details"""
    model = get_object_or_404(AIModel, id=model_id)
    training_logs = ModelTrainingLog.objects.filter(model=model).order_by('-training_date')
    
    context = {
        'model': model,
        'training_logs': training_logs,
    }
    
    return render(request, 'ai_models/model_details.html', context)

def api_model_status(request):
    """API endpoint for model status"""
    models = AIModel.objects.filter(is_active=True)
    
    data = {
        'models': [],
        'total_models': models.count(),
        'trained_models': models.filter(status='trained').count(),
        'overall_status': 'ready' if models.filter(status='trained').exists() else 'not_ready',
    }
    
    for model in models:
        data['models'].append({
            'id': model.id,
            'name': model.name,
            'type': model.model_type,
            'status': model.status,
            'accuracy': model.accuracy,
            'version': model.version,
        })
    
    return JsonResponse(data)

@login_required
def run_inference(request):
    """Run inference on sample data"""
    if request.method == 'POST':
        try:
            model_type = request.POST.get('model_type', 'spiral')
            sample_data = request.POST.get('sample_data', '{}')
            
            predictor = get_predictor()
            
            if model_type == 'spiral':
                # Simulate spiral features
                import random
                features = {
                    'area': random.uniform(0.3, 0.8),
                    'perimeter': random.uniform(0.4, 0.9),
                    'circularity': random.uniform(0.2, 0.7),
                    'aspect_ratio': random.uniform(0.8, 1.2),
                    'bounding_box_area': random.uniform(0.5, 0.9),
                    'filled_ratio': random.uniform(0.6, 0.95),
                    'distance_std': random.uniform(0.1, 0.5),
                }
                prediction = predictor.predict_spiral(features)
                
            elif model_type == 'voice':
                # Simulate voice features
                features = {
                    'jitter': random.uniform(0.1, 0.9),
                    'hnr': random.uniform(5, 25),
                    'zero_crossing_rate': random.uniform(0.01, 0.1),
                    'spectral_centroid_std': random.uniform(100, 1000),
                    'pitch_std': random.uniform(10, 100),
                }
                prediction = predictor.predict_voice(features)
                
            elif model_type == 'quiz':
                # Simulate quiz features
                features = {
                    'motor_score': random.uniform(0, 16),
                    'non_motor_count': random.randint(0, 4),
                    'total_score': random.uniform(0, 100),
                }
                prediction = predictor.predict_quiz(features)
            
            else:
                return JsonResponse({'error': 'Invalid model type'}, status=400)
            
            return JsonResponse({
                'success': True,
                'model_type': model_type,
                'prediction': prediction,
                'features': features,
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)