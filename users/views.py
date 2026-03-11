from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, MedicalHistoryForm
from .models import MedicalHistory

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('home')  # Simple redirect to home
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.userprofile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.userprofile)
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
    }
    return render(request, 'users/profile.html', context)

@login_required
def medical_history(request):
    if request.method == 'POST':
        form = MedicalHistoryForm(request.POST)
        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.patient = request.user
            medical_record.save()
            messages.success(request, 'Medical history added successfully!')
            return redirect('medical_history')
    else:
        form = MedicalHistoryForm()
    
    histories = MedicalHistory.objects.filter(patient=request.user)
    return render(request, 'users/medical_history.html', {'form': form, 'histories': histories})

@login_required
def patient_dashboard(request):
    if request.user.userprofile.user_type != 'patient':
        messages.warning(request, 'Access denied. Patient dashboard only.')
        return redirect('home')
    
    return render(request, 'users/patient_dashboard.html')

@login_required
def doctor_dashboard(request):
    if request.user.userprofile.user_type != 'doctor':
        messages.warning(request, 'Access denied. Doctor dashboard only.')
        return redirect('home')
    
    return render(request, 'users/doctor_dashboard.html')