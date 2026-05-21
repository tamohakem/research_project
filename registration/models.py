from django.db import models
from django.conf import settings
from curriculum.models import Course, CourseProgramme

class CourseRegistration(models.Model):
    STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('dropped', 'Dropped'),
        ('completed', 'Completed'),
    ]
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='registrations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    programme_course = models.ForeignKey(CourseProgramme, on_delete=models.CASCADE, null=True)
    academic_year = models.CharField(max_length=9)
    semester = models.IntegerField(choices=[(1, 'First'), (2, 'Second')])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='registered')
    registered_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'course', 'academic_year', 'semester']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.code} ({self.status})"