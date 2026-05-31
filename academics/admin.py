from django.contrib import admin
from .models import Grade, UserMark

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['grade_letter', 'min_mark', 'max_mark', 'grade_point']
    list_editable = ['grade_point']

@admin.register(UserMark)
class UserMarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'ca_mark', 'exam_mark', 'total_mark', 'grade_letter', 'is_passed']
    list_filter = ['user', 'course', 'semester']
    readonly_fields = ['total_mark', 'grade_letter', 'grade_point', 'is_passed']