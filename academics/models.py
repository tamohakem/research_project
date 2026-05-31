from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

class Grade(models.Model):
    grade_letter = models.CharField(max_length=2, unique=True)
    min_mark = models.DecimalField(max_digits=5, decimal_places=2)
    max_mark = models.DecimalField(max_digits=5, decimal_places=2)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2)
    description = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.grade_letter}: {self.grade_point} points"
    
    class Meta:
        ordering = ['-grade_point']


class UserMark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='marks')
    course = models.ForeignKey('curriculum.Course', on_delete=models.CASCADE)
    ca_mark = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(30)])
    exam_mark = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(70)])
    semester = models.IntegerField(choices=[(1, 'First Semester'), (2, 'Second Semester')])
    academic_year = models.CharField(max_length=9)
    attempt_number = models.IntegerField(default=1)
    exclude_from_cgpa = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'course', 'semester', 'academic_year', 'attempt_number']
        ordering = ['-academic_year', 'semester', 'course__code']
    
    @property
    def total_mark(self):
        """Simple sum of CA and Exam (CA max 30, Exam max 70, total max 100)"""
        return float(self.ca_mark) + float(self.exam_mark)
    
    @property
    def grade_point(self):
        try:
            grade = Grade.objects.get(min_mark__lte=self.total_mark, max_mark__gte=self.total_mark)
            return grade.grade_point
        except Grade.DoesNotExist:
            return 0.00
    
    @property
    def grade_letter(self):
        try:
            grade = Grade.objects.get(min_mark__lte=self.total_mark, max_mark__gte=self.total_mark)
            return grade.grade_letter
        except Grade.DoesNotExist:
            return 'F'
    
    @property
    def is_passed(self):
        """Grade C (50%) is minimum pass for ALL courses"""
        return self.total_mark >= 50