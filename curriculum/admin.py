from django.contrib import admin
from .models import Course, CourseProgramme

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'credits', 'level']
    list_filter = ['level']
    search_fields = ['code', 'title']

@admin.register(CourseProgramme)
class CourseProgrammeAdmin(admin.ModelAdmin):
    list_display = ['programme', 'course', 'year', 'semester', 'level']
    list_filter = ['programme', 'year', 'semester', 'level']
    search_fields = ['programme__name', 'course__code', 'course__title']