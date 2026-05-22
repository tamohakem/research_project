from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from .models import UserMark, Grade
from .calculators import GPACalculator, ProgressTracker
from curriculum.models import Course, CourseProgramme
from registration.models import CourseRegistration


def student_academic_hub(request):
    """Main hub for student academic management (requires login)"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to access your academic hub.')
        return redirect('accounts:login')
    
    if request.user.role not in ['student', 'admin']:
        messages.warning(request, 'This page is for students only.')
        return redirect('dashboard:home')
    
    # Get student's registered courses
    registrations = CourseRegistration.objects.filter(
        student=request.user,
        status='registered'
    ).select_related('course')
    
    # Get marks for registered courses
    marks = UserMark.objects.filter(user=request.user).select_related('course')
    
    registered_courses = []
    for reg in registrations:
        mark = marks.filter(course=reg.course).first()
        registered_courses.append({
            'course': reg.course,
            'has_marks': mark is not None,
            'marks': mark,
            'total_mark': mark.total_mark if mark else None,
            'grade': mark.grade_letter if mark else 'Not entered',
            'is_passed': mark.is_passed if mark else None,
        })
    
    # Available courses (not registered)
    available_courses = []
    if request.user.programme:
        programme_courses = CourseProgramme.objects.filter(
            programme=request.user.programme,
            year=request.user.current_year or 1
        ).select_related('course')
        registered_course_ids = [reg.course_id for reg in registrations]
        available_courses = [cp.course for cp in programme_courses if cp.course.id not in registered_course_ids]
    
    # Calculate current academic standing
    cgpa = GPACalculator.calculate_cumulative_gpa(request.user)
    classification = GPACalculator.get_degree_classification(cgpa)
    completed_credits = ProgressTracker.get_completed_credits(request.user)
    total_credits_needed = request.user.programme.total_credits_required if request.user.programme else 0
    progress_percentage = (completed_credits / total_credits_needed * 100) if total_credits_needed > 0 else 0
    
    # Fix: ensure current_year is an integer (default 1 if not set)
    current_year = request.user.current_year if request.user.current_year else 1
    
    context = {
        'registered_courses': registered_courses,
        'available_courses': available_courses,
        'cgpa': cgpa,
        'classification': classification,
        'completed_credits': completed_credits,
        'total_credits_needed': total_credits_needed,
        'progress_percentage': round(progress_percentage, 1),
        'grading_scale': Grade.objects.all(),
        'current_year': current_year,   # <-- ADDED
    }
    return render(request, 'academics/student_academic_hub.html', context)


def simulate_marks(request):
    # ... (your existing simulate_marks, unchanged)
    pass


def simulation_preview(request):
    # ... (unchanged)
    pass


@login_required
def save_simulation(request):
    # ... (unchanged)
    pass


@login_required
def discard_simulation(request):
    # ... (unchanged)
    pass


@login_required
def select_courses(request):
    # ... (unchanged)
    pass


@login_required
def drop_selected_course(request, registration_id):
    # ... (unchanged)
    pass