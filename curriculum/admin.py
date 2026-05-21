from django.contrib import admin
from .models import Course, CourseProgramme

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'credits', 'status_type']

@admin.register(CourseProgramme)
class CourseProgrammeAdmin(admin.ModelAdmin):
    list_display = ['programme', 'course', 'year', 'semester']