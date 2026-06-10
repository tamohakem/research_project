# face_auth/urls.py
from django.urls import path
from . import views_2fa

app_name = 'face_auth'

urlpatterns = [
    # 2FA Management
    path('settings/', views_2fa.two_factor_settings, name='two_factor_settings'),
    path('delete-photo/', views_2fa.delete_profile_photo, name='delete_profile_photo'),
    path('status/', views_2fa.two_factor_status, name='two_factor_status'),
    
    # 2FA Authentication
    path('2fa-login/', views_2fa.two_factor_login_view, name='two_factor_login'),
    path('verify-face-2fa/', views_2fa.verify_face_2fa, name='verify_face_2fa'),
]