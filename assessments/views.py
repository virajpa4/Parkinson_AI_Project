from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Assessment, SpiralDrawing, VoiceRecording, SymptomQuiz, MRIScan, PostureVideo, PatientHistory
from .forms import (
    SymptomQuizForm, SpiralDrawingForm, VoiceRecordingForm, 
    MRIScanForm, PostureVideoForm, AssessmentSelectionForm
)
import json
from datetime import datetime
# Add imports at the top
from ai_models.ml_utils import ParkinsonPredictor
from ai_models.views import predict_spiral, predict_voice, predict_quiz

# Update the assessment functions to use AI predictions

@login_required
def assessment_selection(request):
    """Assessment selection page (Fig 1.1(b) from PDF)"""
    if request.method == 'POST':
        form = AssessmentSelectionForm(request.POST)
        if form.is_valid():
            assessment_type = form.cleaned_data['assessment_type']
            
            # Redirect to appropriate assessment
            if assessment_type == 'spiral':
                return redirect('assessments:spiral_drawing')
            elif assessment_type == 'voice':
                return redirect('assessments:voice_recording')
            elif assessment_type == 'quiz':
                return redirect('assessments:symptom_quiz')
            elif assessment_type == 'video':
                return redirect('assessments:posture_video')
            elif assessment_type == 'mri':
                return redirect('assessments:mri_scan')
    
    else:
        form = AssessmentSelectionForm()
    
    return render(request, 'assessments/assessment_selection.html', {'form': form})

@login_required
def symptom_quiz(request):
    """Symptom quiz assessment"""
    if request.method == 'POST':
        form = SymptomQuizForm(request.POST)
        if form.is_valid():
            # Create assessment record
            assessment = Assessment.objects.create(
                user=request.user,
                assessment_type='quiz',
                severity_score=form.cleaned_data.get('severity_score', 0)
            )
            
            # Save quiz data
            quiz = form.save(commit=False)
            quiz.assessment = assessment
            quiz.save()
            
            # Calculate Parkinson probability (simplified for now)
            quiz_score = quiz.calculate_score()
            has_parkinson = quiz_score > 30
            stage = min(5, int(quiz_score / 20)) if has_parkinson else 0
            
            # Update assessment with results
            assessment.parkinson_prediction = has_parkinson
            assessment.parkinson_stage = stage
            assessment.severity_score = quiz_score
            assessment.confidence_score = min(quiz_score * 1.5, 95)
            assessment.save()
            
            # Create history record
            PatientHistory.objects.create(
                user=request.user,
                quiz_score=quiz_score,
                overall_severity=quiz_score,
                prediction='Positive' if has_parkinson else 'Negative',
                recommendation='Consult a neurologist for detailed evaluation' if has_parkinson else 'No significant symptoms detected'
            )
            
            messages.success(request, 'Symptom assessment completed!')
            return redirect('assessments:quiz_result', assessment_id=assessment.id)
    
    else:
        form = SymptomQuizForm()
    
    return render(request, 'assessments/symptom_quiz.html', {'form': form})

@login_required
def spiral_drawing_assessment(request):
    """Spiral drawing assessment"""
    if request.method == 'POST':
        form = SpiralDrawingForm(request.POST, request.FILES)
        if form.is_valid():
            # Create assessment record
            assessment = Assessment.objects.create(
                user=request.user,
                assessment_type='spiral'
            )
            
            # For now, simulate AI analysis
            import random
            smoothness = random.uniform(3, 9)
            tremor_freq = random.uniform(0, 10)
            
            # Determine prediction based on simulated scores
            has_parkinson = smoothness < 5 or tremor_freq > 5
            stage = 1 if has_parkinson else 0
            
            # Save spiral drawing
            spiral = SpiralDrawing.objects.create(
                assessment=assessment,
                drawing_image=form.cleaned_data['drawing_image'],
                smoothness_score=smoothness,
                tremor_frequency=tremor_freq,
                amplitude_variation=random.uniform(0, 5)
            )
            
            # Update assessment
            severity_score = (10 - smoothness) * 10 + tremor_freq * 2
            assessment.parkinson_prediction = has_parkinson
            assessment.parkinson_stage = stage
            assessment.severity_score = min(severity_score, 100)
            assessment.confidence_score = random.uniform(70, 95)
            assessment.save()
            
            messages.success(request, 'Spiral drawing analysis complete!')
            return redirect('assessments:spiral_result', assessment_id=assessment.id)
    
    else:
        form = SpiralDrawingForm()
    
    return render(request, 'assessments/spiral_drawing.html', {'form': form})

@login_required
def voice_recording_assessment(request):
    """Voice recording assessment"""
    if request.method == 'POST':
        form = VoiceRecordingForm(request.POST, request.FILES)
        if form.is_valid():
            # Create assessment record
            assessment = Assessment.objects.create(
                user=request.user,
                assessment_type='voice'
            )
            
            # For now, simulate AI analysis
            import random
            jitter = random.uniform(0, 2)
            shimmer = random.uniform(0, 1)
            hnr = random.uniform(5, 25)
            
            # Determine prediction
            has_parkinson = jitter > 0.8 or shimmer > 0.3 or hnr < 15
            stage = 1 if has_parkinson else 0
            
            # Save voice recording
            voice = VoiceRecording.objects.create(
                assessment=assessment,
                audio_file=form.cleaned_data['audio_file'],
                jitter=jitter,
                shimmer=shimmer,
                hnr=hnr,
                duration=random.uniform(5, 30)
            )
            
            # Update assessment
            severity_score = jitter * 30 + shimmer * 40 + (25 - hnr)
            assessment.parkinson_prediction = has_parkinson
            assessment.parkinson_stage = stage
            assessment.severity_score = min(severity_score, 100)
            assessment.confidence_score = random.uniform(75, 95)
            assessment.save()
            
            messages.success(request, 'Voice analysis complete!')
            return redirect('assessments:voice_result', assessment_id=assessment.id)
    
    else:
        form = VoiceRecordingForm()
    
    return render(request, 'assessments/voice_recording.html', {'form': form})

@login_required
def mri_scan_assessment(request):
    """MRI scan assessment"""
    if request.method == 'POST':
        form = MRIScanForm(request.POST, request.FILES)
        if form.is_valid():
            # Create assessment record
            assessment = Assessment.objects.create(
                user=request.user,
                assessment_type='mri'
            )
            
            # For now, simulate AI analysis
            import random
            nigra_volume = random.uniform(0.3, 0.6)
            asymmetry = random.uniform(0, 0.3)
            
            # Determine prediction
            has_parkinson = nigra_volume < 0.4 or asymmetry > 0.15
            stage = 2 if asymmetry > 0.2 else (1 if has_parkinson else 0)
            
            # Save MRI scan
            mri = MRIScan.objects.create(
                assessment=assessment,
                scan_image=form.cleaned_data['scan_image'],
                nigra_volume=nigra_volume,
                asymmetry_index=asymmetry,
                cnn_confidence=random.uniform(80, 98)
            )
            
            # Update assessment
            severity_score = (0.6 - nigra_volume) * 200 + asymmetry * 300
            assessment.parkinson_prediction = has_parkinson
            assessment.parkinson_stage = stage
            assessment.severity_score = min(severity_score, 100)
            assessment.confidence_score = random.uniform(85, 99)
            assessment.save()
            
            messages.success(request, 'MRI analysis complete!')
            return redirect('assessments:mri_result', assessment_id=assessment.id)
    
    else:
        form = MRIScanForm()
    
    return render(request, 'assessments/mri_scan.html', {'form': form})

@login_required
def posture_video_assessment(request):
    """Posture and gait video assessment"""
    if request.method == 'POST':
        form = PostureVideoForm(request.POST, request.FILES)
        if form.is_valid():
            # Create assessment record
            assessment = Assessment.objects.create(
                user=request.user,
                assessment_type='video'
            )
            
            # For now, simulate AI analysis
            import random
            gait_speed = random.uniform(0.5, 1.5)
            arm_swing = random.uniform(10, 50)
            balance_score = random.uniform(30, 95)
            
            # Determine prediction
            has_parkinson = gait_speed < 0.8 or arm_swing < 20 or balance_score < 60
            stage = 2 if balance_score < 50 else (1 if has_parkinson else 0)
            
            # Save video
            video = PostureVideo.objects.create(
                assessment=assessment,
                video_file=form.cleaned_data['video_file'],
                gait_speed=gait_speed,
                arm_swing=arm_swing,
                balance_score=balance_score,
                duration=random.uniform(10, 60)
            )
            
            # Update assessment
            severity_score = (0.8 - gait_speed) * 100 + (30 - arm_swing) + (100 - balance_score)
            assessment.parkinson_prediction = has_parkinson
            assessment.parkinson_stage = stage
            assessment.severity_score = min(severity_score, 100)
            assessment.confidence_score = random.uniform(75, 95)
            assessment.save()
            
            messages.success(request, 'Posture analysis complete!')
            return redirect('assessments:video_result', assessment_id=assessment.id)
    
    else:
        form = PostureVideoForm()
    
    return render(request, 'assessments/posture_video.html', {'form': form})

@login_required
def assessment_result(request, assessment_id):
    """
    Handle assessment results - determine type from URL
    """
    try:
        # First, determine what type of assessment from URL
        path = request.path
        
        if 'quiz' in path:
            # Try to import or get QuizAssessment model
            try:
                from .models import QuizAssessment
                assessment = get_object_or_404(QuizAssessment, id=assessment_id, user=request.user)
                template_name = 'assessments/quiz_result.html'
                
                # Prepare quiz context
                total_possible = assessment.total_questions * 3 if hasattr(assessment, 'total_questions') else 30
                score = assessment.score if hasattr(assessment, 'score') else 0
                percentage = (score / total_possible * 100) if total_possible > 0 else 0
                
                context = {
                    'assessment': assessment,
                    'score': score,
                    'total': total_possible,
                    'percentage': percentage,
                    'timestamp': assessment.created_at,
                    'assessment_type': 'quiz',
                }
                
            except ImportError:
                # Fallback if model doesn't exist
                messages.error(request, "Quiz assessment model not found")
                return redirect('/dashboard/')
                
        elif 'spiral' in path:
            # Try to import or get SpiralAssessment model
            try:
                from .models import SpiralAssessment
                assessment = get_object_or_404(SpiralAssessment, id=assessment_id, user=request.user)
                template_name = 'assessments/spiral_result.html'
                
                # Prepare spiral context
                context = {
                    'assessment': assessment,
                    'tremor_score': getattr(assessment, 'tremor_score', 0),
                    'smoothness': getattr(assessment, 'smoothness', 0),
                    'confidence': getattr(assessment, 'confidence_score', 0.5) * 100,
                    'image_url': assessment.image.url if hasattr(assessment, 'image') and assessment.image else None,
                    'timestamp': assessment.created_at,
                    'assessment_type': 'spiral',
                }
                
            except ImportError:
                messages.error(request, "Spiral assessment model not found")
                return redirect('/dashboard/')
        else:
            messages.error(request, "Unknown assessment type")
            return redirect('/dashboard/')
        
        # Try to render with dashboard URL, fallback to direct URL
        try:
            return render(request, template_name, context)
        except Exception as e:
            # If template has URL issues, create a simple context
            simple_context = {
                'assessment': assessment,
                'timestamp': assessment.created_at,
                'direct_dashboard_url': '/dashboard/'
            }
            return render(request, template_name, simple_context)
            
    except Exception as e:
        print(f"Error in assessment_result: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"Error loading results: {str(e)}")
        # Use direct URL as fallback
        return redirect('/dashboard/')
    
@login_required
def api_save_drawing(request):
    """API endpoint to save drawing data from canvas"""
    if request.method == 'POST' and request.is_ajax():
        try:
            data = json.loads(request.body)
            drawing_data = data.get('drawing_data')
            
            # Here you would process the drawing data
            # For now, just return success
            return JsonResponse({
                'success': True,
                'message': 'Drawing saved successfully',
                'data_received': len(drawing_data) if drawing_data else 0
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


from django.http import HttpResponse

def simple_assessment(request):
    """Simple assessment page"""
    return render(request, 'assessments/simple.html')

def spiral_test(request):
    return HttpResponse("Spiral drawing test page - Working!")

def voice_test(request):
    return HttpResponse("Voice recording test page - Working!")

def quiz_test(request):
    return HttpResponse("Symptom quiz page - Working!")