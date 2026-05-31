from django.contrib import admin
from .models import Department, Programme, User

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    search_fields = ['name', 'code']

@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ['department', 'degree_type', 'name', 'option_name', 'duration_years', 'is_top_up', 'is_active']
    list_filter = ['department', 'degree_type', 'is_top_up', 'is_active']
    search_fields = ['name', 'option_name']

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'programme']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']