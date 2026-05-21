from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from curriculum.models import Course

class Grade(models.Model):
    grade_letter = models.CharField(max_length=2, unique=True)
    min_mark = models.DecimalField(max_digits=5, decimal_places=2)
    max_mark = models.DecimalField(max_digits=5, decimal_places=2)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2)
    description = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.grade_letter}: {self.grade_point} points"
    
    class Meta:
        ordering = ['-grade_point']


class UserMark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marks')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    ca_mark = models.DecimalField(max_digits=5, decimal_places=2)
    exam_mark = models.DecimalField(max_digits=5, decimal_places=2)
    semester = models.IntegerField(choices=[(1, 'First Semester'), (2, 'Second Semester')])
    academic_year = models.CharField(max_length=9)
    attempt_number = models.IntegerField(default=1)
    exclude_from_cgpa = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'course', 'semester', 'academic_year', 'attempt_number']
    
    @property
    def total_mark(self):
        total = (self.ca_mark * self.course.ca_weight + self.exam_mark * self.course.exam_weight) / 100
        return round(total, 2)
    
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
        if self.course.status_type == 'Compulsory':
            return self.total_mark >= 50
        else:
            return self.total_mark >= 40