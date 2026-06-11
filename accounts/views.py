from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from .forms import UserRegistrationForm, UserLoginForm
from face_auth.models import UserFaceProfile
import logging
import pickle

logger = logging.getLogger(__name__)

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            profile_photo = form.face_photo
            enable_face_auth = form.cleaned_data.get('enable_face_auth')

            if profile_photo and form.face_encoding is not None:
                UserFaceProfile.objects.create(
                    user=user,
                    profile_photo=profile_photo,
                    face_encoding=pickle.dumps(form.face_encoding),
                    two_factor_enabled=enable_face_auth
                )
            login(request, user)
            if profile_photo:
                status = 'enabled' if enable_face_auth else 'set up'
                messages.success(request, f'Welcome {user.get_full_name()}! Face authentication is {status}.')
            else:
                messages.success(request, f'Welcome {user.get_full_name()}!')
            return redirect('dashboard:home')
        logger.warning("Registration form invalid: %s", form.errors.as_json())
        messages.error(request, 'Registration could not be completed. Please review the highlighted errors below.')
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
            try:
                face_profile = user.face_profile
            except UserFaceProfile.DoesNotExist:
                face_profile = None

            if (
                face_profile
                and face_profile.two_factor_enabled
                and face_profile.has_face_registered
                and face_profile.face_encoding
            ):
                request.session['2fa_pending_user_id'] = user.id
                request.session['2fa_pending_username'] = user.username
                cache.delete(failed_key)
                return render(request, 'face_auth/face_verification.html', {
                    'username': user.username,
                    'requires_2fa': True
                })

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
