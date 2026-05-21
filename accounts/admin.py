from django.contrib import admin
from .models import User, Programme

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role']
    list_filter = ['role']

@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'degree_type']