from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from accounts.models import User, Programme
from curriculum.models import Course, CourseProgramme
from registration.models import CourseRegistration
from academics.models import UserMark
from academics.calculators import GPACalculator

@login_required
@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with statistics and management options"""
    
    # Statistics
    total_students = User.objects.filter(role='student').count()
    total_graduates = User.objects.filter(role='graduate').count()
    total_courses = Course.objects.count()
    total_programmes = Programme.objects.count()
    
    # Registration statistics
    total_registrations = CourseRegistration.objects.count()
    pending_registrations = CourseRegistration.objects.filter(status='registered').count()
    completed_registrations = CourseRegistration.objects.filter(status='completed').count()
    
    # Recent registrations (last 7 days)
    recent_registrations = CourseRegistration.objects.select_related('student', 'course').order_by('-registered_date')[:10]
    
    # Students without programme assigned
    students_no_programme = User.objects.filter(role='student', programme__isnull=True).count()
    
    # Course registration popularity
    popular_courses = CourseRegistration.objects.values('course__code', 'course__title').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Students by year
    students_by_year = User.objects.filter(role='student').values('current_year').annotate(
        count=Count('id')
    ).order_by('current_year')
    
    # Programme distribution
    programme_distribution = Programme.objects.annotate(
        student_count=Count('user', filter=Q(user__role='student'))
    ).values('code', 'student_count')
    
    context = {
        'total_students': total_students,
        'total_graduates': total_graduates,
        'total_courses': total_courses,
        'total_programmes': total_programmes,
        'total_registrations': total_registrations,
        'pending_registrations': pending_registrations,
        'completed_registrations': completed_registrations,
        'recent_registrations': recent_registrations,
        'students_no_programme': students_no_programme,
        'popular_courses': popular_courses,
        'students_by_year': students_by_year,
        'programme_distribution': programme_distribution,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
@staff_member_required
def manage_students(request):
    """View and manage all students"""
    
    students = User.objects.filter(role='student').select_related('programme').order_by('-date_joined')
    
    # Filter by programme
    programme_id = request.GET.get('programme')
    if programme_id:
        students = students.filter(programme_id=programme_id)
    
    # Filter by year
    year = request.GET.get('year')
    if year:
        students = students.filter(current_year=year)
    
    programmes = Programme.objects.all()
    
    context = {
        'students': students,
        'programmes': programmes,
        'selected_programme': programme_id,
        'selected_year': year,
    }
    return render(request, 'dashboard/manage_students.html', context)


@login_required
@staff_member_required
def edit_student(request, student_id):
    """Edit student details"""
    
    student = get_object_or_404(User, id=student_id, role='student')
    
    if request.method == 'POST':
        student.first_name = request.POST.get('first_name')
        student.last_name = request.POST.get('last_name')
        student.email = request.POST.get('email')
        student.programme_id = request.POST.get('programme') or None
        student.current_year = request.POST.get('current_year') or None
        student.student_id = request.POST.get('student_id')
        student.phone_number = request.POST.get('phone_number')
        student.save()
        
        messages.success(request, f'Student {student.get_full_name()} updated successfully!')
        return redirect('dashboard:manage_students')
    
    programmes = Programme.objects.all()
    years = [(1, 'Year 1'), (2, 'Year 2'), (3, 'Year 3'), (4, 'Year 4')]
    
    context = {
        'student': student,
        'programmes': programmes,
        'years': years,
    }
    return render(request, 'dashboard/edit_student.html', context)


@login_required
@staff_member_required
def manage_registrations(request):
    """View and manage all course registrations"""
    
    registrations = CourseRegistration.objects.select_related('student', 'course').order_by('-registered_date')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        registrations = registrations.filter(status=status)
    
    # Filter by programme
    programme_id = request.GET.get('programme')
    if programme_id:
        registrations = registrations.filter(student__programme_id=programme_id)
    
    programmes = Programme.objects.all()
    status_choices = CourseRegistration.STATUS_CHOICES
    
    context = {
        'registrations': registrations,
        'programmes': programmes,
        'status_choices': status_choices,
        'selected_status': status,
        'selected_programme': programme_id,
    }
    return render(request, 'dashboard/manage_registrations.html', context)


@login_required
@staff_member_required
def approve_registration(request, registration_id):
    """Approve a pending registration (if using approval workflow)"""
    
    registration = get_object_or_404(CourseRegistration, id=registration_id)
    registration.status = 'registered'
    registration.save()
    
    messages.success(request, f'Registration for {registration.course.code} approved for {registration.student.get_full_name()}')
    return redirect('dashboard:manage_registrations')


@login_required
@staff_member_required
def admin_drop_course(request, registration_id):
    """Admin drop a student from a course"""
    
    registration = get_object_or_404(CourseRegistration, id=registration_id)
    course_code = registration.course.code
    student_name = registration.student.get_full_name()
    
    if request.method == 'POST':
        registration.delete()
        messages.success(request, f'Dropped {student_name} from {course_code}')
        return redirect('dashboard:manage_registrations')
    
    context = {
        'registration': registration,
        'student_name': student_name,
        'course_code': course_code,
    }
    return render(request, 'dashboard/confirm_drop.html', context)


@login_required
@staff_member_required
def student_details(request, student_id):
    """View detailed student information including registration history"""
    
    student = get_object_or_404(User, id=student_id, role='student')
    
    # Get all registrations
    registrations = CourseRegistration.objects.filter(student=student).select_related('course').order_by('-academic_year', '-semester')
    
    # Get marks entered
    marks = UserMark.objects.filter(user=student).select_related('course').order_by('-academic_year', '-semester')
    
    # Calculate CGPA
    cgpa = GPACalculator.calculate_cumulative_gpa(student)
    classification = GPACalculator.get_degree_classification(cgpa)
    
    # Registration by semester
    registrations_by_semester = registrations.values('academic_year', 'semester').annotate(count=Count('id'))
    
    context = {
        'student': student,
        'registrations': registrations,
        'marks': marks,
        'cgpa': cgpa,
        'classification': classification,
        'registrations_by_semester': registrations_by_semester,
    }
    return render(request, 'dashboard/student_details.html', context)


@login_required
@staff_member_required
def bulk_assign_programme(request):
    """Bulk assign programme to multiple students"""
    
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        programme_id = request.POST.get('programme')
        year = request.POST.get('year')
        
        if student_ids and programme_id:
            programme = get_object_or_404(Programme, id=programme_id)
            students = User.objects.filter(id__in=student_ids, role='student')
            
            for student in students:
                student.programme = programme
                if year:
                    student.current_year = year
                student.save()
            
            messages.success(request, f'{students.count()} students assigned to {programme.code}')
        else:
            messages.error(request, 'Please select students and a programme')
        
        return redirect('dashboard:manage_students')
    
    students_without_programme = User.objects.filter(role='student', programme__isnull=True)
    programmes = Programme.objects.all()
    
    context = {
        'students': students_without_programme,
        'programmes': programmes,
    }
    return render(request, 'dashboard/bulk_assign.html', context)