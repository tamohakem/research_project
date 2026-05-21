from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Course, CourseProgramme
from accounts.models import Programme

@login_required
def course_list_view(request):
    programme_id = request.GET.get('programme')
    year = request.GET.get('year')
    semester = request.GET.get('semester')
    
    courses = CourseProgramme.objects.select_related('course', 'programme').all()
    
    if programme_id:
        courses = courses.filter(programme_id=programme_id)
    if year:
        courses = courses.filter(year=year)
    if semester:
        courses = courses.filter(semester=semester)
    
    paginator = Paginator(courses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    programmes = Programme.objects.all()
    
    context = {
        'page_obj': page_obj,
        'programmes': programmes,
        'selected_programme': programme_id,
        'selected_year': year,
        'selected_semester': semester,
    }
    return render(request, 'curriculum/course_list.html', context)


@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    offered_in = CourseProgramme.objects.filter(course=course).select_related('programme')
    
    context = {
        'course': course,
        'offered_in': offered_in,
    }
    return render(request, 'curriculum/course_detail.html', context)