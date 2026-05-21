from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from academics.calculators import GPACalculator, ProgressTracker
from academics.models import UserMark

@login_required
def home_view(request):
    cgpa = GPACalculator.calculate_cumulative_gpa(request.user)
    classification = GPACalculator.get_degree_classification(cgpa)
    completed_credits = ProgressTracker.get_completed_credits(request.user)
    total_credits = request.user.programme.total_credits_required if request.user.programme else 0
    progress_percentage = (completed_credits / total_credits * 100) if total_credits > 0 else 0
    remaining_count = ProgressTracker.get_remaining_courses(request.user).count()
    
    recent_marks = UserMark.objects.filter(user=request.user).select_related('course').order_by('-created_at')[:5]
    
    context = {
        'cgpa': cgpa,
        'classification': classification,
        'completed_credits': completed_credits,
        'total_credits_required': total_credits,
        'progress_percentage': round(progress_percentage, 1),
        'remaining_courses_count': remaining_count,
        'recent_marks': recent_marks,
    }
    return render(request, 'dashboard/home.html', context)