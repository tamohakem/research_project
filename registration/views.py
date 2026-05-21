from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from curriculum.models import Course, CourseProgramme
from accounts.models import Programme
from .models import CourseRegistration

@login_required
def course_catalog_view(request):
    """View all available courses for student's programme"""
    
    if not request.user.programme:
        messages.warning(request, 'Please contact admin to assign a programme to your account first.')
        return redirect('dashboard:home')
    
    # Get current academic year and semester
    academic_year = request.GET.get('academic_year', '2024-2025')
    semester = int(request.GET.get('semester', 1))
    year = int(request.GET.get('year', request.user.current_year or 1))
    
    # Get courses available for this programme and year
    available_courses = CourseProgramme.objects.filter(
        programme=request.user.programme,
        year=year,
        semester=semester
    ).select_related('course')
    
    # Get courses already registered by student
    registered_ids = CourseRegistration.objects.filter(
        student=request.user,
        academic_year=academic_year,
        semester=semester
    ).values_list('course_id', flat=True)
    
    # Mark which courses are registered
    for cp in available_courses:
        cp.is_registered = cp.course.id in registered_ids
    
    context = {
        'available_courses': available_courses,
        'registered_ids': registered_ids,
        'academic_year': academic_year,
        'semester': semester,
        'year': year,
        'current_year': request.user.current_year or 1,
        'programme': request.user.programme,
    }
    return render(request, 'registration/course_catalog.html', context)


@login_required
def register_course(request, course_id):
    """Register student for a course"""
    
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        academic_year = request.POST.get('academic_year', '2024-2025')
        semester = int(request.POST.get('semester', 1))
        
        # Check if already registered
        existing, created = CourseRegistration.objects.get_or_create(
            student=request.user,
            course=course,
            academic_year=academic_year,
            semester=semester,
            defaults={'status': 'registered'}
        )
        
        if created:
            messages.success(request, f'Successfully registered for {course.code} - {course.title}')
        else:
            messages.info(request, f'You are already registered for {course.code}')
        
        return redirect('registration:course_catalog')


@login_required
def drop_course(request, registration_id):
    """Drop a registered course"""
    
    registration = get_object_or_404(CourseRegistration, id=registration_id, student=request.user)
    
    if request.method == 'POST':
        course_code = registration.course.code
        registration.delete()
        messages.success(request, f'Successfully dropped {course_code}')
        return redirect('registration:my_courses')


@login_required
def my_courses_view(request):
    """View student's registered courses"""
    
    academic_year = request.GET.get('academic_year', '2024-2025')
    semester = int(request.GET.get('semester', 1))
    
    registrations = CourseRegistration.objects.filter(
        student=request.user,
        academic_year=academic_year,
        semester=semester
    ).select_related('course')
    
    total_credits = sum(reg.course.credits for reg in registrations if reg.status == 'registered')
    
    context = {
        'registrations': registrations,
        'total_credits': total_credits,
        'academic_year': academic_year,
        'semester': semester,
    }
    return render(request, 'registration/my_courses.html', context)