import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fet_project.settings')
django.setup()

from apps.accounts.models import Programme, User
from apps.academics.models import Grade

def create_programmes():
    programmes = [
        {'code': 'BENG-CE', 'name': 'BEng Computer Engineering', 'degree_type': 'Bachelor', 'total_credits_required': 240, 'duration_years': 4},
        {'code': 'BENG-EEE', 'name': 'BEng Electrical Engineering', 'degree_type': 'Bachelor', 'total_credits_required': 240, 'duration_years': 4},
        {'code': 'BENG-ME', 'name': 'BEng Mechanical Engineering', 'degree_type': 'Bachelor', 'total_credits_required': 240, 'duration_years': 4},
        {'code': 'BENG-CE', 'name': 'BEng Civil Engineering', 'degree_type': 'Bachelor', 'total_credits_required': 240, 'duration_years': 4},
    ]
    
    for prog in programmes:
        Programme.objects.get_or_create(code=prog['code'], defaults=prog)
    print("✓ Programmes created")

def create_grading_scale():
    grades = [
        ('A', 80, 100, 4.00),
        ('B+', 70, 79, 3.50),
        ('B', 60, 69, 3.00),
        ('C+', 55, 59, 2.50),
        ('C', 50, 54, 2.00),
        ('D+', 45, 49, 1.50),
        ('D', 40, 44, 