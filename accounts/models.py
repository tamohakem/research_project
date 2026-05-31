from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser

class Department(models.Model):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    established_year = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Programme(models.Model):
    DEGREE_TYPES = [
        ('BENG', 'Bachelor of Engineering (BEng)'),
        ('TOPUP_BENG', 'Top-up Bachelor of Engineering'),
        ('MENG', 'Master of Engineering (MEng)'),
        ('TOPUP_MENG', 'Top-up Master of Engineering'),
        ('MSC_ENG', 'Master of Science in Engineering (MSc Eng)'),
        ('TOPUP_MSC', 'Top-up Master of Science'),
        ('PHD', 'Doctor of Philosophy (PhD)'),
    ]
    
    DEGREE_LEVELS = [
        ('UNDERGRADUATE', 'Undergraduate'),
        ('MASTERS', 'Masters'),
        ('DOCTORAL', 'Doctoral'),
    ]
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programmes')
    degree_type = models.CharField(max_length=20, choices=DEGREE_TYPES)
    degree_level = models.CharField(max_length=20, choices=DEGREE_LEVELS, default='UNDERGRADUATE')
    name = models.CharField(max_length=200)
    option_name = models.CharField(max_length=200, blank=True, help_text="Specialization/Option")
    duration_years = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    duration_semesters = models.IntegerField(default=8, help_text="Total semesters for the programme")
    is_top_up = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['department', 'degree_type', 'name', 'option_name']
        ordering = ['department', 'degree_level', 'degree_type', 'name', 'option_name']
    
    def __str__(self):
        top_up_display = " (TOP-UP)" if self.is_top_up else ""
        if self.option_name:
            return f"{self.get_degree_type_display()} - {self.name} ({self.option_name}){top_up_display}"
        return f"{self.get_degree_type_display()} - {self.name}{top_up_display}"
    
    def get_available_levels(self):
        """Return the list of academic levels available for this programme based on degree type"""
        if self.degree_type in ['BENG', 'TOPUP_BENG']:
            return [200, 300, 400, 500]
        elif self.degree_type in ['MENG', 'MSC_ENG', 'TOPUP_MENG', 'TOPUP_MSC']:
            return [600]
        elif self.degree_type == 'PHD':
            return [700]
        return [200, 300, 400, 500]
    
    def get_display_duration(self):
        """Return formatted duration string"""
        if self.is_top_up:
            return f"TOP-UP: {self.duration_years} year(s)"
        return f"{self.duration_years} years"
    
    def get_semester_count(self):
        """Return total number of semesters in the programme"""
        return self.duration_semesters


class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Current Student'),
        ('graduate', 'Graduate'),
        ('admin', 'Administrator'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    programme = models.ForeignKey(Programme, on_delete=models.SET_NULL, null=True, blank=True)
    current_year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)], null=True, blank=True)
    current_semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)], null=True, blank=True)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    enrollment_date = models.DateField(null=True, blank=True)
    expected_graduation_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        programme_info = f" - {self.programme.name}" if self.programme else " - No Programme"
        if self.programme and self.programme.option_name:
            programme_info = f" - {self.programme.name} ({self.programme.option_name})"
        return f"{self.get_full_name()} ({self.username}){programme_info}"
    
    def is_graduate_user(self):
        return self.role == 'graduate'
    
    def is_student_user(self):
        return self.role == 'student'
    
    class Meta:
        ordering = ['last_name', 'first_name']