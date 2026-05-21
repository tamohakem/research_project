from django.contrib import admin
from .models import Grade, UserMark

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['grade_letter', 'min_mark', 'max_mark', 'grade_point']

@admin.register(UserMark)
class UserMarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'total_mark']