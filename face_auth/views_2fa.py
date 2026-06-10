# face_auth/views_2fa.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, get_user_model  # Added get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.files.base import ContentFile
import json
import base64
import binascii
import pickle

from .models import UserFaceProfile, TwoFactorAuthLog
from .forms import TwoFactorSettingsForm
from .fasiva import (
    AUTH_METHOD,
    BLINK_EVIDENCE_REQUIRED,
    MAX_FAILED_ATTEMPTS,
    MIN_LIVENESS_CONFIDENCE,
)
from .image_capture import image_from_data_url

# Get the custom User model from your accounts app
User = get_user_model()

def get_face_comparator():
    try:
        from .face_comparator import face_comparator
        return face_comparator, None
    except ModuleNotFoundError as exc:
        return None, f"Face authentication is unavailable because a dependency is missing: {exc.name}."

def frame_from_data_url(image_data):
    try:
        import cv2
        import numpy as np
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            f'Face verification is unavailable because a dependency is missing: {exc.name}.'
        ) from exc

    try:
        _, imgstr = image_data.split(';base64,', 1)
        image_bytes = base64.b64decode(imgstr)
    except (ValueError, TypeError, binascii.Error) as exc:
        raise ValueError('Could not decode image data') from exc

    nparr = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

@login_required
def two_factor_settings(request):
    """View for users to manage their 2FA settings"""
    profile, created = UserFaceProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = TwoFactorSettingsForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            captured_photo = image_from_data_url(
                request.POST.get('captured_face_image'),
                'settings-face'
            )
            uploaded_photo = request.FILES.get('profile_photo')
            photo = uploaded_photo or captured_photo

            # Check if profile photo is being uploaded
            if photo:
                face_comparator, dependency_error = get_face_comparator()

                if dependency_error:
                    messages.error(request, dependency_error)
                    return render(request, 'face_auth/two_factor_settings.html', {
                        'form': form,
                        'profile': profile,
                        'has_face': profile.has_face_registered
                    })
                
                # Extract face encoding from uploaded photo
                encoding, success, message = face_comparator.extract_face_encoding(photo)
                
                if success:
                    # Save the photo and encoding
                    profile.profile_photo = photo
                    profile.face_encoding = pickle.dumps(encoding)
                    profile.two_factor_enabled = form.cleaned_data['two_factor_enabled']
                    profile.save()
                    
                    messages.success(request, 
                        f"✓ Profile photo saved successfully! {message}\n"
                        f"2FA has been {'enabled' if profile.two_factor_enabled else 'disabled'}."
                    )
                else:
                    messages.error(request, f"Could not save profile photo: {message}")
                    
                    return render(request, 'face_auth/two_factor_settings.html', {
                        'form': form,
                        'profile': profile,
                        'has_face': profile.has_face_registered
                    })
            else:
                # Just update 2FA status without changing photo
                if form.cleaned_data['two_factor_enabled'] and not profile.has_face_registered:
                    messages.error(request, "Upload or snap a face photo before enabling two-factor authentication.")
                    return render(request, 'face_auth/two_factor_settings.html', {
                        'form': form,
                        'profile': profile,
                        'has_face': profile.has_face_registered
                    })

                profile.two_factor_enabled = form.cleaned_data['two_factor_enabled']
                profile.save()
                messages.success(request, 
                    f"Two-factor authentication has been {'enabled' if profile.two_factor_enabled else 'disabled'}."
                )
            
            return redirect('face_auth:two_factor_settings')
    else:
        form = TwoFactorSettingsForm(instance=profile)
    
    return render(request, 'face_auth/two_factor_settings.html', {
        'form': form,
        'profile': profile,
        'has_face': profile.has_face_registered
    })

@login_required
def delete_profile_photo(request):
    """Delete the user's profile photo and disable 2FA"""
    if request.method == 'POST':
        profile = request.user.face_profile
        if profile.profile_photo:
            profile.profile_photo.delete()
        profile.face_encoding = None
        profile.two_factor_enabled = False
        profile.save()
        
        messages.success(request, "Profile photo deleted. Two-factor authentication has been disabled.")
    
    return redirect('face_auth:two_factor_settings')

def two_factor_login_view(request):
    """Custom login view that implements 2FA with face verification"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # First factor: Username and password
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user has 2FA enabled
            try:
                profile = UserFaceProfile.objects.get(user=user)
                
                if profile.two_factor_enabled and profile.has_face_registered and profile.face_encoding:
                    # Store user ID in session for 2FA verification
                    request.session['2fa_pending_user_id'] = user.id
                    request.session['2fa_pending_username'] = user.username
                    
                    # Redirect to face verification page
                    return render(request, 'face_auth/face_verification.html', {
                        'username': user.username,
                        'requires_2fa': True
                    })
                else:
                    # No 2FA enabled, log in directly
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.username}!")
                    
                    TwoFactorAuthLog.objects.create(
                        user=user,
                        success=True,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    return redirect('dashboard:home')
                    
            except UserFaceProfile.DoesNotExist:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('dashboard:home')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'face_auth/two_factor_login.html')

@csrf_exempt
@require_http_methods(["POST"])
def verify_face_2fa(request):
    """API endpoint for face verification as second factor"""
    try:
        data = json.loads(request.body)
        image_data = data.get('image')
        blink_image_data = data.get('blink_image')
        
        if not image_data:
            return JsonResponse({'success': False, 'message': 'No image data received'})
        
        # Get pending user ID from session
        user_id = request.session.get('2fa_pending_user_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': 'Session expired. Please login again.'})
        
        # Use get_user_model() instead of importing User directly
        user = User.objects.get(id=user_id)  # Now User is defined at the top
        
        # Get user's profile and stored face encoding
        try:
            profile = UserFaceProfile.objects.get(user=user)
            
            if not profile.has_face_registered or not profile.face_encoding:
                return JsonResponse({'success': False, 'message': 'No face profile found for 2FA'})

            if profile.failed_2fa_attempts >= MAX_FAILED_ATTEMPTS:
                return JsonResponse({
                    'success': False,
                    'message': 'Too many failed attempts. Please reset your password or contact support.'
                })

            face_comparator, dependency_error = get_face_comparator()
            if dependency_error:
                return JsonResponse({'success': False, 'message': dependency_error})

            try:
                frame = frame_from_data_url(image_data)
                blink_frame = frame_from_data_url(blink_image_data) if blink_image_data else None
            except (RuntimeError, ValueError) as exc:
                return JsonResponse({'success': False, 'message': str(exc)})
            
            if frame is None:
                return JsonResponse({'success': False, 'message': 'Could not process image'})

            is_live, liveness_confidence = face_comparator.detect_liveness(frame)
            blink_details = (
                face_comparator.analyze_blink_evidence(frame, blink_frame)
                if blink_frame is not None
                else {'available': False, 'blink_detected': False}
            )
            if BLINK_EVIDENCE_REQUIRED and not blink_details.get('blink_detected'):
                is_live = False
            if not is_live or liveness_confidence < MIN_LIVENESS_CONFIDENCE:
                message = 'Camera quality check failed. Use a clear, well-lit live face image and try again.'
                TwoFactorAuthLog.objects.create(
                    user=user,
                    success=False,
                    error_message=message,
                    failure_reason='liveness_failed',
                    details={
                        'methodology': AUTH_METHOD,
                        'stage': 'liveness_check',
                        'liveness_confidence': round(liveness_confidence, 2),
                        'minimum_liveness_confidence': MIN_LIVENESS_CONFIDENCE,
                        'presence': face_comparator.last_liveness_details,
                        'blink': blink_details,
                        'blink_required': BLINK_EVIDENCE_REQUIRED,
                    },
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                profile.failed_2fa_attempts += 1
                profile.save()
                return JsonResponse({
                    'success': False,
                    'message': message,
                    'attempts_left': MAX_FAILED_ATTEMPTS - profile.failed_2fa_attempts
                })
            
            # Extract encoding from captured face
            captured_encoding, face_detected, message = face_comparator.extract_face_encoding(frame)
            
            if not face_detected:
                TwoFactorAuthLog.objects.create(
                    user=user,
                    success=False,
                    error_message=message,
                    failure_reason='face_detection_failed',
                    details={
                        'methodology': AUTH_METHOD,
                        'stage': 'face_extraction',
                    },
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                profile.failed_2fa_attempts += 1
                profile.save()
                
                return JsonResponse({'success': False, 'message': message})
            
            # Compare with stored encoding
            stored_encoding = pickle.loads(profile.face_encoding)
            match, distance, confidence = face_comparator.compare_faces(
                stored_encoding, 
                captured_encoding
            )
            
            # Log the attempt
            TwoFactorAuthLog.objects.create(
                user=user,
                success=match,
                confidence_score=confidence,
                error_message='' if match else f'Face mismatch',
                auth_method=AUTH_METHOD,
                failure_reason='' if match else 'face_mismatch',
                details={
                    'methodology': AUTH_METHOD,
                    'stage': 'face_comparison',
                    'liveness_confidence': round(liveness_confidence, 2),
                    'presence': face_comparator.last_liveness_details,
                    'blink': blink_details,
                    'scores': face_comparator.last_match_details,
                },
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            if match:
                # Success - login the user
                login(request, user)
                
                # Clear 2FA session data
                del request.session['2fa_pending_user_id']
                del request.session['2fa_pending_username']
                
                # Update profile
                profile.last_2fa_used = timezone.now()
                profile.failed_2fa_attempts = 0
                profile.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Face verified successfully! Redirecting...',
                    'confidence': round(confidence, 2)
                })
            else:
                # Failed verification
                profile.failed_2fa_attempts += 1
                profile.save()
                
                if profile.failed_2fa_attempts >= MAX_FAILED_ATTEMPTS:
                    return JsonResponse({
                        'success': False,
                        'message': 'Too many failed attempts. Please reset your password or contact support.'
                    })
                
                return JsonResponse({
                    'success': False,
                    'message': f'Face verification failed (confidence: {confidence:.1f}%). Please try again.',
                    'attempts_left': MAX_FAILED_ATTEMPTS - profile.failed_2fa_attempts
                })
                
        except UserFaceProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': '2FA not set up for this account'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Verification error: {str(e)}'})

@login_required
def two_factor_status(request):
    """Check if current user has 2FA enabled"""
    try:
        profile = request.user.face_profile
        return JsonResponse({
            'enabled': profile.two_factor_enabled,
            'has_face': profile.has_face_registered,
            'last_used': profile.last_2fa_used,
            'failed_attempts': profile.failed_2fa_attempts
        })
    except:
        return JsonResponse({'enabled': False, 'has_face': False})

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
