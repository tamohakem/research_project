from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from .models import UserMark, Grade
from .calculators import GPACalculator, ProgressTracker
from curriculum.models import Course, CourseProgramme


@login_required
def marks_entry_view(request):
    if request.user.role == 'graduate':
        messages.warning(request, 'Graduates cannot enter new marks.')
        return redirect('dashboard:home')
    
    # Get current academic year and semester
    academic_year = request.GET.get('academic_year', '2024-2025')
    semester = int(request.GET.get('semester', 1))
    
    # Get ALL courses for the user's programme and current year
    courses = []
    if request.user.programme:
        course_programmes = CourseProgramme.objects.filter(
            programme=request.user.programme,
            year=request.user.current_year or 1
        ).select_related('course')
        courses = [cp.course for cp in course_programmes]
    else:
        messages.warning(request, 'No programme assigned to your account. Please contact admin.')
    
    # Handle form submission
    if request.method == 'POST':
        with transaction.atomic():
            for key, value in request.POST.items():
                if key.startswith('ca_'):
                    course_id = key.split('_')[1]
                    ca_mark = value
                    exam_mark = request.POST.get(f'exam_{course_id}')
                    
                    if ca_mark and exam_mark:
                        try:
                            course = Course.objects.get(id=course_id)
                            mark, created = UserMark.objects.update_or_create(
                                user=request.user,
                                course=course,
                                semester=semester,
                                academic_year=academic_year,
                                defaults={
                                    'ca_mark': Decimal(ca_mark),
                                    'exam_mark': Decimal(exam_mark),
                                }
                            )
                        except Exception as e:
                            messages.error(request, f'Error saving marks for course: {e}')
            
            messages.success(request, 'Marks saved successfully!')
            return redirect('academics:marks_entry')
    
    # Get existing marks for this student
    existing_marks = {}
    for mark in UserMark.objects.filter(
        user=request.user,
        academic_year=academic_year,
        semester=semester
    ):
        existing_marks[mark.course_id] = mark
    
    context = {
        'courses': courses,
        'existing_marks': existing_marks,
        'academic_year': academic_year,
        'semester': semester,
        'current_year': request.user.current_year or 1,
        'has_courses': len(courses) > 0,
    }
    return render(request, 'academics/marks_entry.html', context)


@login_required
def academic_summary_view(request):
    semesters = GPACalculator.get_semester_gpas(request.user)
    
    cgpa = GPACalculator.calculate_cumulative_gpa(request.user)
    classification = GPACalculator.get_degree_classification(cgpa)
    
    recent_marks = UserMark.objects.filter(user=request.user).select_related('course')[:10]
    
    context = {
        'semester_gpas': semesters,
        'cgpa': cgpa,
        'classification': classification,
        'recent_marks': recent_marks,
        'grading_scale': Grade.objects.all(),
    }
    return render(request, 'academics/academic_summary.html', context)


@login_required
def progress_view(request):
    """
    Display graduation progress based on passed courses.
    Completed Credits: Sum of credits from all passed courses (Grade C or above)
    Remaining Credits: Total Required Credits - Completed Credits
    Progress Percentage: (Completed Credits / Total Required Credits) * 100
    """
    from curriculum.models import CourseProgramme
    
    # Get programme information
    programme = request.user.programme
    if programme:
        total_credits_required = programme.total_credits_required
    else:
        total_credits_required = 0
    
    # Calculate completed credits based on passed courses
    completed_credits = ProgressTracker.get_completed_credits(request.user)
    
    # Calculate remaining credits
    remaining_credits = total_credits_required - completed_credits
    if remaining_credits < 0:
        remaining_credits = 0
    
    # Calculate progress percentage
    if total_credits_required > 0:
        progress_percentage = (completed_credits / total_credits_required) * 100
    else:
        progress_percentage = 0
    
    # Get remaining courses (not yet passed)
    remaining_courses = ProgressTracker.get_remaining_courses(request.user)
    
    # Get passed courses with their average grades
    all_marks = UserMark.objects.filter(
        user=request.user,
        exclude_from_cgpa=False
    ).select_related('course')
    
    # Group by course and calculate average percentage
    course_results = {}
    for mark in all_marks:
        course_id = mark.course.id
        if course_id not in course_results:
            course_results[course_id] = {
                'course': mark.course,
                'totals': []
            }
        course_results[course_id]['totals'].append(float(mark.total_mark))
    
    # Determine passed courses (average >= 50%)
    passed_courses = []
    for course_id, data in course_results.items():
        avg_percentage = sum(data['totals']) / len(data['totals'])
        if avg_percentage >= 50:  # Pass threshold for ALL courses
            # Determine grade based on average
            if avg_percentage >= 80:
                grade = 'A'
                grade_point = 4.00
            elif avg_percentage >= 70:
                grade = 'B+'
                grade_point = 3.50
            elif avg_percentage >= 60:
                grade = 'B'
                grade_point = 3.00
            elif avg_percentage >= 55:
                grade = 'C+'
                grade_point = 2.50
            elif avg_percentage >= 50:
                grade = 'C'
                grade_point = 2.00
            else:
                grade = 'F'
                grade_point = 0.00
            
            passed_courses.append({
                'code': data['course'].code,
                'title': data['course'].title,
                'credits': data['course'].credits,
                'grade': grade,
                'grade_point': grade_point,
                'avg_percentage': round(avg_percentage, 2)
            })
    
    # Sort passed courses by code
    passed_courses.sort(key=lambda x: x['code'])
    
    context = {
        'completed_credits': completed_credits,
        'remaining_credits': remaining_credits,
        'total_credits_required': total_credits_required,
        'progress_percentage': round(progress_percentage, 1),
        'remaining_courses': remaining_courses,
        'total_remaining': remaining_courses.count(),
        'passed_courses': passed_courses,
    }
    return render(request, 'academics/progress.html', context)