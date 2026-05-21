from django.contrib import admin
from .models import CourseRegistration

@admin.register(CourseRegistration)
class CourseRegistrationAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'academic_year', 'semester', 'status']
    list_filter = ['status', 'academic_year', 'semester']
    search_fields = ['student__username', 'course__code']