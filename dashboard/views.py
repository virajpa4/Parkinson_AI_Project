from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Max, Min, Count
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    PatientDashboard, ProgressChart, DoctorPatientMapping,
    Alert, ProgressGoal, TreatmentPlan
)
from assessments.models import Assessment, PatientHistory
from .forms import ProgressGoalForm, TreatmentPlanForm, PatientSelectionForm, AlertForm

@login_required
def dashboard_home(request):
    """Main dashboard view based on user role"""
    user = request.user
    
    if hasattr(user, 'userprofile'):
        if user.userprofile.user_type == 'doctor':
            return redirect('dashboard:doctor_dashboard')
        elif user.userprofile.user_type == 'patient':
            return redirect('dashboard:patient_dashboard')
    
    # Default dashboard for admin or unspecified users
    return render(request, 'dashboard/admin_dashboard.html')

@login_required
def patient_dashboard(request):
    """Patient's personal dashboard"""
    # Get or create patient dashboard
    dashboard, created = PatientDashboard.objects.get_or_create(
        user=request.user,
        defaults={'overall_risk_score': 0}
    )
    
    # Update dashboard metrics
    dashboard.update_dashboard()
    
    # Get assessment history
    assessments = Assessment.objects.filter(user=request.user).order_by('-date_taken')[:10]
    
    # Get recent alerts
    alerts = Alert.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    
    # Get active goals
    goals = ProgressGoal.objects.filter(patient=request.user, is_completed=False)
    
    # Get active treatment plans
    treatment_plans = TreatmentPlan.objects.filter(patient=request.user, is_active=True)
    
    # Get progress data for charts
    progress_data = get_progress_data(request.user)
    
    context = {
        'dashboard': dashboard,
        'assessments': assessments,
        'alerts': alerts,
        'goals': goals,
        'treatment_plans': treatment_plans,
        'progress_data': progress_data,
    }
    
    return render(request, 'dashboard/patient_dashboard.html', context)

@login_required
def doctor_dashboard(request):
    """Doctor's dashboard to monitor multiple patients"""
    # Verify user is a doctor
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'doctor':
        messages.error(request, 'Access denied. Doctor dashboard only.')
        return redirect('home')
    
    # Get assigned patients
    patient_mappings = DoctorPatientMapping.objects.filter(
        doctor=request.user, 
        is_active=True
    ).select_related('patient')
    
    # Get patient stats
    patients_data = []
    for mapping in patient_mappings:
        patient = mapping.patient
        # Get latest assessment
        latest_assessment = Assessment.objects.filter(
            user=patient
        ).order_by('-date_taken').first()
        
        # Get unread alerts for this patient
        unread_alerts = Alert.objects.filter(
            user=patient, 
            is_read=False
        ).count()
        
        patients_data.append({
            'patient': patient,
            'mapping': mapping,
            'latest_assessment': latest_assessment,
            'unread_alerts': unread_alerts,
            'last_activity': latest_assessment.date_taken if latest_assessment else None,
        })
    
    # Get system alerts
    system_alerts = Alert.objects.filter(
        alert_type='system',
        is_read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'patients_data': patients_data,
        'system_alerts': system_alerts,
        'total_patients': len(patients_data),
    }
    
    return render(request, 'dashboard/doctor_dashboard.html', context)

@login_required
def patient_detail(request, patient_id):
    """Doctor's view of specific patient details"""
    # Verify user is a doctor
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'doctor':
        messages.error(request, 'Access denied. Doctor dashboard only.')
        return redirect('home')
    
    # Verify doctor has access to this patient
    patient = get_object_or_404(User, id=patient_id)
    DoctorPatientMapping.objects.get(
        doctor=request.user,
        patient=patient,
        is_active=True
    )
    
    # Get patient dashboard
    dashboard, created = PatientDashboard.objects.get_or_create(user=patient)
    dashboard.update_dashboard()
    
    # Get patient assessments
    assessments = Assessment.objects.filter(user=patient).order_by('-date_taken')
    
    # Get patient history
    history = PatientHistory.objects.filter(user=patient).order_by('-assessment_date')[:20]
    
    # Get goals
    goals = ProgressGoal.objects.filter(patient=patient)
    
    # Get treatment plans
    treatment_plans = TreatmentPlan.objects.filter(patient=patient)
    
    # Get alerts
    alerts = Alert.objects.filter(user=patient).order_by('-created_at')[:10]
    
    # Progress data for charts
    progress_data = get_progress_data(patient)
    
    context = {
        'patient': patient,
        'dashboard': dashboard,
        'assessments': assessments,
        'history': history,
        'goals': goals,
        'treatment_plans': treatment_plans,
        'alerts': alerts,
        'progress_data': progress_data,
    }
    
    return render(request, 'dashboard/patient_detail.html', context)

@login_required
def progress_charts(request):
    """Progress charts and visualization"""
    user = request.user
    
    # Get progress data
    progress_data = get_progress_data(user)
    
    # Get assessment types data
    assessment_types_data = get_assessment_types_data(user)
    
    context = {
        'progress_data': progress_data,
        'assessment_types_data': assessment_types_data,
    }
    
    return render(request, 'dashboard/progress_charts.html', context)

@login_required
def add_progress_goal(request):
    """Add a new progress goal"""
    if request.method == 'POST':
        form = ProgressGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.patient = request.user
            goal.start_date = timezone.now().date()
            goal.save()
            
            messages.success(request, 'Progress goal added successfully!')
            return redirect('dashboard:patient_dashboard')
    else:
        form = ProgressGoalForm()
    
    return render(request, 'dashboard/add_goal.html', {'form': form})

@login_required
def update_goal_progress(request, goal_id):
    """Update goal progress"""
    goal = get_object_or_404(ProgressGoal, id=goal_id, patient=request.user)
    
    if request.method == 'POST':
        current_value = request.POST.get('current_value')
        try:
            goal.current_value = float(current_value)
            if goal.current_value >= goal.target_value:
                goal.is_completed = True
                goal.completed_date = timezone.now().date()
            goal.save()
            
            messages.success(request, 'Goal progress updated!')
            return JsonResponse({'success': True, 'progress': goal.progress_percentage()})
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid value'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def mark_alert_read(request, alert_id):
    """Mark an alert as read"""
    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    alert.is_read = True
    alert.read_at = timezone.now()
    alert.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Alert marked as read')
    return redirect('dashboard:patient_dashboard')

@login_required
def send_alert(request, patient_id):
    """Doctor sends alert to patient"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    patient = get_object_or_404(User, id=patient_id)
    
    # Verify doctor has access to this patient
    DoctorPatientMapping.objects.get(
        doctor=request.user,
        patient=patient,
        is_active=True
    )
    
    if request.method == 'POST':
        form = AlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = patient
            alert.save()
            
            messages.success(request, f'Alert sent to {patient.username}')
            return redirect('dashboard:patient_detail', patient_id=patient_id)
    else:
        form = AlertForm()
    
    return render(request, 'dashboard/send_alert.html', {'form': form, 'patient': patient})

@login_required
def api_progress_data(request):
    """API endpoint for progress chart data"""
    user = request.user
    days = int(request.GET.get('days', 30))  # Default 30 days
    
    data = get_progress_data(user, days)
    return JsonResponse(data)

# Helper functions
def get_progress_data(user, days=30):
    """Generate progress data for charts"""
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get assessments in date range
    assessments = Assessment.objects.filter(
        user=user,
        date_taken__range=[start_date, end_date]
    ).order_by('date_taken')
    
    # Prepare data for line chart
    dates = []
    scores = []
    
    for assessment in assessments:
        dates.append(assessment.date_taken.strftime('%Y-%m-%d'))
        scores.append(assessment.severity_score)
    
    # Get average scores by assessment type
    type_data = {}
    for assessment in assessments:
        assessment_type = assessment.get_assessment_type_display()
        if assessment_type not in type_data:
            type_data[assessment_type] = []
        type_data[assessment_type].append(assessment.severity_score)
    
    type_averages = {}
    for atype, scores_list in type_data.items():
        if scores_list:
            type_averages[atype] = sum(scores_list) / len(scores_list)
    
    return {
        'dates': dates,
        'scores': scores,
        'type_averages': type_averages,
        'total_assessments': len(assessments),
        'average_score': sum(scores) / len(scores) if scores else 0,
        'highest_score': max(scores) if scores else 0,
        'lowest_score': min(scores) if scores else 0,
    }

def get_assessment_types_data(user):
    """Get data by assessment type"""
    assessments = Assessment.objects.filter(user=user)
    
    type_counts = {}
    type_scores = {}
    
    for assessment in assessments:
        atype = assessment.get_assessment_type_display()
        type_counts[atype] = type_counts.get(atype, 0) + 1
        
        if atype not in type_scores:
            type_scores[atype] = []
        type_scores[atype].append(assessment.severity_score)
    
    # Calculate averages
    type_data = []
    for atype, count in type_counts.items():
        scores = type_scores.get(atype, [])
        avg_score = sum(scores) / len(scores) if scores else 0
        type_data.append({
            'type': atype,
            'count': count,
            'avg_score': round(avg_score, 2),
        })
    
    return type_data