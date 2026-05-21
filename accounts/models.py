from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Programme(models.Model):
    DEGREE_TYPES = [
        ('Bachelor', 'Bachelor of Engineering'),
        ('Master', 'Master of Engineering'),
        ('PhD', 'Doctor of Philosophy'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    degree_type = models.CharField(max_length=10, choices=DEGREE_TYPES)
    total_credits_required = models.IntegerField(validators=[MinValueValidator(120), MaxValueValidator(240)])
    duration_years = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        ordering = ['degree_type', 'code']


class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Current Student'),
        ('graduate', 'Graduate'),
        ('admin', 'Administrator'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    programme = models.ForeignKey(Programme, on_delete=models.SET_NULL, null=True, blank=True)
    current_year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)], null=True, blank=True)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def is_graduate_user(self):
        return self.role == 'graduate'
    
    def is_student_user(self):
        return self.role == 'student'
    
    class Meta:
        ordering = ['last_name', 'first_name']