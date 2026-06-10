# face_auth/forms.py
from django import forms
from .models import UserFaceProfile

class TwoFactorSettingsForm(forms.ModelForm):
    class Meta:
        model = UserFaceProfile
        fields = ['two_factor_enabled', 'profile_photo']
        widgets = {
            'two_factor_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'twoFactorToggle'
            }),
            'profile_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'profilePhoto',
                'accept': 'image/*'
            })
        }
        labels = {
            'two_factor_enabled': 'Enable Two-Factor Authentication (Face Recognition)',
            'profile_photo': 'Profile Photo for 2FA'
        }
        help_texts = {
            'profile_photo': 'Upload a clear, front-facing photo of your face. This will be used for verification.',
            'two_factor_enabled': 'When enabled, you will need to verify your face after entering your password.'
        }