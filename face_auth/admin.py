# face_auth/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import UserFaceProfile, TwoFactorAuthLog

User = get_user_model()

@admin.register(UserFaceProfile)
class UserFaceProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'two_factor_enabled', 'has_face_registered', 'created_at']
    list_filter = ['two_factor_enabled', 'created_at']
    search_fields = ['user__username', 'user__email']

@admin.register(TwoFactorAuthLog)
class TwoFactorAuthLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'success', 'confidence_score', 'timestamp']
    list_filter = ['success', 'timestamp']
    search_fields = ['user__username']