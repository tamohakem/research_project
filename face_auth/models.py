# face_auth/models.py
from django.db import models
from django.conf import settings  # Use this instead of direct User import

from .fasiva import AUTH_METHOD

class UserFaceProfile(models.Model):
    """Store user's profile photo and face encoding for 2FA"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Changed from 'User' to settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='face_profile'
    )
    profile_photo = models.ImageField(
        upload_to='profile_photos/', 
        null=True, 
        blank=True,
        help_text="Upload a clear photo of your face for 2FA"
    )
    face_encoding = models.BinaryField(null=True, blank=True)
    two_factor_enabled = models.BooleanField(
        default=False,
        help_text="Enable two-factor authentication with face recognition"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_2fa_used = models.DateTimeField(null=True, blank=True)
    failed_2fa_attempts = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'user_face_profiles'
    
    def __str__(self):
        return f"{self.user.username} - 2FA: {'Enabled' if self.two_factor_enabled else 'Disabled'}"
    
    @property
    def has_face_registered(self):
        return self.profile_photo is not None and bool(self.profile_photo)

class TwoFactorAuthLog(models.Model):
    """Log all 2FA attempts"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Changed from 'User' to settings.AUTH_USER_MODEL
        on_delete=models.CASCADE
    )
    success = models.BooleanField(default=False)
    confidence_score = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    auth_method = models.CharField(max_length=50, default=AUTH_METHOD)
    failure_reason = models.TextField(blank=True)
    details = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'two_factor_auth_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.timestamp} - {'Success' if self.success else 'Failed'}"
