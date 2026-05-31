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
    
    academic_year = request.GET.get('academic_year', '2024-2025')
    semester = int(request.GET.get('semester', 1))
    
    courses = []
    if request.user.programme:
        course_programmes = CourseProgramme.objects.filter(
            programme=request.user.programme,
            year=request.user.current_year or 1
        ).select_related('course')
        courses = [cp.course for cp in course_programmes]
    else:
        messages.warning(request, 'No programme assigned to your account.')
    
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
                            messages.error(request, f'Error saving marks: {e}')
            
            messages.success(request, 'Marks saved successfully!')
            return redirect('academics:marks_entry')
    
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
    """Display graduation progress based on passed courses."""
    from curriculum.models import CourseProgramme
    
    # Get total credits required based on degree type
    if request.user.programme:
        degree_type = request.user.programme.degree_type
        if degree_type in ['BENG', 'TOPUP_BENG']:
            total_credits_required = 240
        elif degree_type in ['MENG', 'MSC_ENG', 'TOPUP_MENG', 'TOPUP_MSC']:
            total_credits_required = 120
        elif degree_type == 'PHD':
            total_credits_required = 180
        else:
            total_credits_required = 240
    else:
        total_credits_required = 0
    
    # Calculate completed credits
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
    
    # Get remaining courses
    remaining_courses = ProgressTracker.get_remaining_courses(request.user)
    
    # Get passed courses with grades
    all_marks = UserMark.objects.filter(
        user=request.user,
        exclude_from_cgpa=False
    ).select_related('course')
    
    course_results = {}
    for mark in all_marks:
        course_id = mark.course.id
        if course_id not in course_results:
            course_results[course_id] = {
                'course': mark.course,
                'totals': []
            }
        course_results[course_id]['totals'].append(float(mark.total_mark))
    
    passed_courses = []
    for course_id, data in course_results.items():
        avg_percentage = sum(data['totals']) / len(data['totals'])
        if avg_percentage >= 50:
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