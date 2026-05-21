from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from .models import UserMark, Grade
from .calculators import GPACalculator, ProgressTracker
from curriculum.models import Course, CourseProgramme
from registration.models import CourseRegistration


@login_required
def student_academic_hub(request):
    """Main hub for student academic management"""
    
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
    
    # Separate courses into categories
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
    
    context = {
        'registered_courses': registered_courses,
        'available_courses': available_courses,
        'cgpa': cgpa,
        'classification': classification,
        'completed_credits': completed_credits,
        'total_credits_needed': total_credits_needed,
        'progress_percentage': round(progress_percentage, 1),
        'grading_scale': Grade.objects.all(),
    }
    return render(request, 'academics/student_academic_hub.html', context)


@login_required
def select_courses(request):
    """Student selects courses from available pool"""
    
    if request.method == 'POST':
        selected_course_ids = request.POST.getlist('course_ids')
        academic_year = request.POST.get('academic_year', '2024-2025')
        semester = int(request.POST.get('semester', 1))
        
        for course_id in selected_course_ids:
            course = get_object_or_404(Course, id=course_id)
            CourseRegistration.objects.get_or_create(
                student=request.user,
                course=course,
                academic_year=academic_year,
                semester=semester,
                defaults={'status': 'registered'}
            )
        
        messages.success(request, f'Successfully registered for {len(selected_course_ids)} course(s)!')
        return redirect('academics:student_hub')
    
    # GET request - show available courses
    registered_course_ids = CourseRegistration.objects.filter(
        student=request.user,
        status='registered'
    ).values_list('course_id', flat=True)
    
    # Get courses for student's programme and year
    available_courses = []
    if request.user.programme:
        programme_courses = CourseProgramme.objects.filter(
            programme=request.user.programme,
            year=request.user.current_year or 1
        ).select_related('course')
        
        for cp in programme_courses:
            if cp.course.id not in registered_course_ids:
                available_courses.append(cp)
    
    context = {
        'available_courses': available_courses,
        'current_year': request.user.current_year or 1,
        'programme': request.user.programme,
    }
    return render(request, 'academics/select_courses.html', context)


@login_required
def drop_selected_course(request, registration_id):
    """Drop a selected course"""
    
    registration = get_object_or_404(CourseRegistration, id=registration_id, student=request.user)
    course_code = registration.course.code
    
    if request.method == 'POST':
        registration.delete()
        messages.success(request, f'Successfully dropped {course_code}')
        return redirect('academics:student_hub')
    
    context = {
        'registration': registration,
        'course_code': course_code,
    }
    return render(request, 'academics/confirm_drop.html', context)


@login_required
def simulate_marks(request):
    """Simulate academic situation with what-if scenarios"""
    
    if request.method == 'POST':
        selected_courses = request.POST.getlist('selected_courses')
        simulation_data = {}
        
        for course_id in selected_courses:
            ca_mark = request.POST.get(f'ca_{course_id}')
            exam_mark = request.POST.get(f'exam_{course_id}')
            if ca_mark and exam_mark:
                simulation_data[int(course_id)] = {
                    'ca_mark': float(ca_mark),
                    'exam_mark': float(exam_mark),
                }
        
        request.session['simulation_data'] = simulation_data
        request.session['simulation_active'] = True
        
        return redirect('academics:simulation_preview')
    
    registered_courses = CourseRegistration.objects.filter(
        student=request.user,
        status='registered'
    ).select_related('course')
    
    context = {
        'courses': [reg.course for reg in registered_courses],
        'grading_scale': Grade.objects.all(),
    }
    return render(request, 'academics/simulate_marks.html', context)


@login_required
def simulation_preview(request):
    """Preview simulated academic results"""
    
    simulation_data = request.session.get('simulation_data', {})
    
    if not simulation_data:
        messages.warning(request, 'No simulation data found.')
        return redirect('academics:simulate_marks')
    
    simulated_results = []
    current_marks = UserMark.objects.filter(user=request.user).select_related('course')
    
    current_total_points = 0
    current_total_credits = 0
    for mark in current_marks:
        if mark.is_passed:
            current_total_points += mark.grade_point * mark.course.credits
            current_total_credits += mark.course.credits
    
    current_cgpa = current_total_points / current_total_credits if current_total_credits > 0 else 0
    
    simulated_total_points = current_total_points
    simulated_total_credits = current_total_credits
    
    for course_id, marks in simulation_data.items():
        course = Course.objects.get(id=course_id)
        total_mark = (marks['ca_mark'] * course.ca_weight + marks['exam_mark'] * course.exam_weight) / 100
        
        try:
            grade = Grade.objects.get(min_mark__lte=total_mark, max_mark__gte=total_mark)
            grade_point = grade.grade_point
            grade_letter = grade.grade_letter
            is_passed = total_mark >= 50
        except:
            grade_point = 0
            grade_letter = 'F'
            is_passed = False
        
        simulated_results.append({
            'course': course,
            'ca_mark': marks['ca_mark'],
            'exam_mark': marks['exam_mark'],
            'total_mark': round(total_mark, 2),
            'grade_letter': grade_letter,
            'grade_point': grade_point,
            'is_passed': is_passed,
        })
        
        if is_passed:
            simulated_total_points += grade_point * course.credits
            simulated_total_credits += course.credits
    
    simulated_cgpa = simulated_total_points / simulated_total_credits if simulated_total_credits > 0 else 0
    
    context = {
        'simulated_results': simulated_results,
        'current_cgpa': round(current_cgpa, 2),
        'simulated_cgpa': round(simulated_cgpa, 2),
        'cgpa_change': round(simulated_cgpa - current_cgpa, 3),
        'grading_scale': Grade.objects.all(),
    }
    return render(request, 'academics/simulation_preview.html', context)


@login_required
def save_simulation(request):
    """Save simulated marks to database"""
    
    simulation_data = request.session.get('simulation_data', {})
    
    if not simulation_data:
        messages.warning(request, 'No simulation data to save.')
        return redirect('academics:student_hub')
    
    with transaction.atomic():
        for course_id, marks in simulation_data.items():
            course = Course.objects.get(id=course_id)
            UserMark.objects.update_or_create(
                user=request.user,
                course=course,
                semester=1,
                academic_year='2024-2025',
                defaults={
                    'ca_mark': Decimal(str(marks['ca_mark'])),
                    'exam_mark': Decimal(str(marks['exam_mark'])),
                }
            )
    
    request.session['simulation_active'] = False
    request.session['simulation_data'] = {}
    
    messages.success(request, 'Your marks have been saved successfully!')
    return redirect('academics:student_hub')


@login_required
def discard_simulation(request):
    """Discard simulated marks"""
    
    request.session['simulation_active'] = False
    request.session['simulation_data'] = {}
    
    messages.info(request, 'Simulation discarded.')
    return redirect('academics:student_hub')