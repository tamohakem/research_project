from django.db import models

class Course(models.Model):
    LEVEL_CHOICES = [
        (200, '200 Level'),
        (300, '300 Level'),
        (400, '400 Level'),
        (500, '500 Level'),
        (600, '600 Level'),
        (700, '700 Level'),
    ]

    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    credits = models.IntegerField()
    level = models.IntegerField(choices=LEVEL_CHOICES, default=200)
    ca_weight = models.IntegerField(default=30)
    exam_weight = models.IntegerField(default=70)

    def __str__(self):
        return f'{self.code}: {self.title}'


class CourseProgramme(models.Model):
    programme = models.ForeignKey('accounts.Programme', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    year = models.IntegerField()
    semester = models.IntegerField(choices=[(1, 'First'), (2, 'Second')])
    level = models.IntegerField(choices=Course.LEVEL_CHOICES, default=200)
    is_core = models.BooleanField(default=True)

    class Meta:
        unique_together = ['programme', 'course', 'year', 'semester']

    def __str__(self):
        return f'Year {self.year}, Sem {self.semester}: {self.course.code}'
