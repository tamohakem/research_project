from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import Programme

class Course(models.Model):
    STATUS_TYPES = [
        ('Compulsory', 'Compulsory'),
        ('Required', 'Required'),
        ('Elective', 'Elective'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    credits = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    status_type = models.CharField(max_length=10, choices=STATUS_TYPES)
    description = models.TextField(blank=True)
    ca_weight = models.IntegerField(default=30)
    exam_weight = models.IntegerField(default=70)
    
    def __str__(self):
        return f"{self.code}: {self.title}"
    
    class Meta:
        ordering = ['code']


class CourseProgramme(models.Model):
    SEMESTER_CHOICES = [(1, 'First Semester'), (2, 'Second Semester')]
    
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    semester = models.IntegerField(choices=SEMESTER_CHOICES)
    is_core = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['programme', 'course', 'year', 'semester']
    
    def __str__(self):
        return f"{self.programme.code} - Year {self.year}, Sem {self.semester}: {self.course.code}"