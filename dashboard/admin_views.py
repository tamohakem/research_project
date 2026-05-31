from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from accounts.models import User, Programme, Department
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
    total_departments = Department.objects.count()
    
    # Registration statistics
    total_registrations = CourseRegistration.objects.count()
    pending_registrations = CourseRegistration.objects.filter(status='registered').count()
    completed_registrations = CourseRegistration.objects.filter(status='completed').count()
    
    # Recent registrations
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
    
    # Programme distribution by department
    programme_distribution = Department.objects.annotate(
        programme_count=Count('programmes'),
        student_count=Count('programmes__user', filter=Q(programmes__user__role='student'))
    ).values('code', 'name', 'programme_count', 'student_count')
    
    # Get all departments for the template
    departments = Department.objects.all().prefetch_related('programmes')
    
    context = {
        'total_students': total_students,
        'total_graduates': total_graduates,
        'total_courses': total_courses,
        'total_programmes': total_programmes,
        'total_departments': total_departments,
        'total_registrations': total_registrations,
        'pending_registrations': pending_registrations,
        'completed_registrations': completed_registrations,
        'recent_registrations': recent_registrations,
        'students_no_programme': students_no_programme,
        'popular_courses': popular_courses,
        'students_by_year': students_by_year,
        'programme_distribution': programme_distribution,
        'departments': departments,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
@staff_member_required
def manage_students(request):
    """View and manage all students"""
    
    students = User.objects.filter(role='student').select_related('programme', 'programme__department').order_by('-date_joined')
    
    # Filter by department
    department_id = request.GET.get('department')
    if department_id:
        students = students.filter(programme__department_id=department_id)
    
    # Filter by programme
    programme_id = request.GET.get('programme')
    if programme_id:
        students = students.filter(programme_id=programme_id)
    
    # Filter by year
    year = request.GET.get('year')
    if year:
        students = students.filter(current_year=year)
    
    departments = Department.objects.all()
    programmes = Programme.objects.all()
    
    context = {
        'students': students,
        'departments': departments,
        'programmes': programmes,
        'selected_department': department_id,
        'selected_programme': programme_id,
        'selected_year': year,
    }
    return render(request, 'dashboard/manage_students.html', context)


@login_required
@staff_member_required
def manage_departments(request):
    """View and manage departments"""
    departments = Department.objects.all().prefetch_related('programmes')
    
    context = {
        'departments': departments,
    }
    return render(request, 'dashboard/manage_departments.html', context)


@login_required
@staff_member_required
def manage_programmes(request):
    """View and manage academic programmes"""
    programmes = Programme.objects.select_related('department').all()
    
    # Filter by department
    dept_id = request.GET.get('department')
    if dept_id:
        programmes = programmes.filter(department_id=dept_id)
    
    # Filter by degree type
    degree_type = request.GET.get('degree_type')
    if degree_type:
        programmes = programmes.filter(degree_type=degree_type)
    
    departments = Department.objects.all()
    degree_choices = Programme.DEGREE_TYPES
    
    context = {
        'programmes': programmes,
        'departments': departments,
        'degree_choices': degree_choices,
        'selected_dept': dept_id,
        'selected_degree': degree_type,
    }
    return render(request, 'dashboard/manage_programmes.html', context)


@login_required
@staff_member_required
def add_programme(request):
    """Add a new academic programme"""
    if request.method == 'POST':
        department_id = request.POST.get('department')
        degree_type = request.POST.get('degree_type')
        name = request.POST.get('name')
        option_name = request.POST.get('option_name')
        duration_years = request.POST.get('duration_years')
        payment_status = request.POST.get('payment_status')
        total_credits = request.POST.get('total_credits')
        is_top_up = request.POST.get('is_top_up') == 'on'
        entry_requirements = request.POST.get('entry_requirements')
        
        department = Department.objects.get(id=department_id)
        
        # Generate code
        base_code = f"{department.code}_{degree_type}"
        if option_name:
            code = f"{base_code}_{option_name.replace(' ', '_')}".upper()
        else:
            code = f"{base_code}_GEN".upper()
        
        Programme.objects.create(
            department=department,
            degree_type=degree_type,
            name=name,
            option_name=option_name,
            code=code,
            duration_years=duration_years,
            payment_status=payment_status,
            total_credits_required=total_credits or (240 if 'BENG' in degree_type else (120 if 'MENG' in degree_type or 'MSC' in degree_type else 180)),
            is_top_up=is_top_up,
            entry_requirements=entry_requirements,
        )
        messages.success(request, 'Programme added successfully!')
        return redirect('dashboard:manage_programmes')
    
    departments = Department.objects.all()
    degree_choices = Programme.DEGREE_TYPES
    payment_choices = Programme.PAYMENT_STATUS
    
    context = {
        'departments': departments,
        'degree_choices': degree_choices,
        'payment_choices': payment_choices,
    }
    return render(request, 'dashboard/add_programme.html', context)


@login_required
@staff_member_required
def programme_details(request, programme_id):
    """View detailed programme information"""
    programme = get_object_or_404(Programme, id=programme_id)
    students = User.objects.filter(programme=programme, role='student')
    courses = CourseProgramme.objects.filter(programme=programme).select_related('course')
    
    context = {
        'programme': programme,
        'students': students,
        'students_count': students.count(),
        'courses': courses,
        'courses_count': courses.count(),
    }
    return render(request, 'dashboard/programme_details.html', context)


@login_required
@staff_member_required
def edit_programme(request, programme_id):
    """Edit programme details"""
    programme = get_object_or_404(Programme, id=programme_id)
    
    if request.method == 'POST':
        programme.degree_type = request.POST.get('degree_type')
        programme.name = request.POST.get('name')
        programme.option_name = request.POST.get('option_name')
        programme.duration_years = request.POST.get('duration_years')
        programme.payment_status = request.POST.get('payment_status')
        programme.total_credits_required = request.POST.get('total_credits')
        programme.is_top_up = request.POST.get('is_top_up') == 'on'
        programme.entry_requirements = request.POST.get('entry_requirements')
        programme.is_active = request.POST.get('is_active') == 'on'
        programme.save()
        
        messages.success(request, 'Programme updated successfully!')
        return redirect('dashboard:manage_programmes')
    
    degree_choices = Programme.DEGREE_TYPES
    payment_choices = Programme.PAYMENT_STATUS
    
    context = {
        'programme': programme,
        'degree_choices': degree_choices,
        'payment_choices': payment_choices,
    }
    return render(request, 'dashboard/edit_programme.html', context)


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
    years = [(1, 'Year 1'), (2, 'Year 2'), (3, 'Year 3'), (4, 'Year 4'), (5, 'Year 5'), (6, 'Year 6')]
    
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
    
    # Filter by department
    department_id = request.GET.get('department')
    if department_id:
        registrations = registrations.filter(student__programme__department_id=department_id)
    
    departments = Department.objects.all()
    status_choices = CourseRegistration.STATUS_CHOICES
    
    context = {
        'registrations': registrations,
        'departments': departments,
        'status_choices': status_choices,
        'selected_status': status,
        'selected_department': department_id,
    }
    return render(request, 'dashboard/manage_registrations.html', context)


@login_required
@staff_member_required
def student_details(request, student_id):
    """View detailed student information including registration history"""
    student = get_object_or_404(User, id=student_id, role='student')
    
    registrations = CourseRegistration.objects.filter(student=student).select_related('course').order_by('-academic_year', '-semester')
    marks = UserMark.objects.filter(user=student).select_related('course').order_by('-academic_year', '-semester')
    cgpa = GPACalculator.calculate_cumulative_gpa(student)
    classification = GPACalculator.get_degree_classification(cgpa)
    
    context = {
        'student': student,
        'registrations': registrations,
        'marks': marks,
        'cgpa': cgpa,
        'classification': classification,
    }
    return render(request, 'dashboard/student_details.html', context)


@login_required
@staff_member_required
def approve_registration(request, registration_id):
    """Approve a pending registration"""
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
    
    if request.method == 'POST':
        course_code = registration.course.code
        student_name = registration.student.get_full_name()
        registration.delete()
        messages.success(request, f'Dropped {student_name} from {course_code}')
        return redirect('dashboard:manage_registrations')
    
    context = {
        'registration': registration,
        'student_name': registration.student.get_full_name(),
        'course_code': registration.course.code,
    }
    return render(request, 'dashboard/confirm_drop.html', context)


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