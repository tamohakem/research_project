from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from academics.calculators import GPACalculator, ProgressTracker
from academics.models import UserMark

@login_required
def home_view(request):
    user = request.user
    cgpa = GPACalculator.calculate_cumulative_gpa(user)
    classification = GPACalculator.get_degree_classification(cgpa)
    completed_credits = ProgressTracker.get_completed_credits(user)
    
    # Get total credits required based on degree type
    if user.programme:
        degree_type = user.programme.degree_type
        if degree_type in ['BENG', 'TOPUP_BENG']:
            total_credits = 240
        elif degree_type in ['MENG', 'MSC_ENG', 'TOPUP_MENG', 'TOPUP_MSC']:
            total_credits = 120
        elif degree_type == 'PHD':
            total_credits = 180
        else:
            total_credits = 240
    else:
        total_credits = 240
    
    progress_percentage = (completed_credits / total_credits * 100) if total_credits > 0 else 0
    remaining_count = ProgressTracker.get_remaining_courses(user).count()
    recent_marks = UserMark.objects.filter(user=user).select_related('course').order_by('-created_at')[:5]
    
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