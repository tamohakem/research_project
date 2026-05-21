from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from .forms import UserRegistrationForm, UserLoginForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.get_full_name()}!')
            return redirect('dashboard:home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    ip_address = request.META.get('REMOTE_ADDR')
    failed_key = f'failed_logins_{ip_address}'
    failed_attempts = cache.get(failed_key, 0)
    
    if failed_attempts >= 5:
        messages.error(request, 'Too many failed login attempts. Please try again after 15 minutes.')
        return render(request, 'accounts/login.html')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            cache.delete(failed_key)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            return redirect('dashboard:home')
        else:
            failed_attempts += 1
            cache.set(failed_key, failed_attempts, 900)
            messages.error(request, f'Invalid username or password. Attempt {failed_attempts} of 5.')
    
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('index')