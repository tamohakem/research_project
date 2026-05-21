from django.urls import path
from . import views
from . import student_views

app_name = 'academics'

urlpatterns = [
    # Existing URLs
    path('marks/entry/', views.marks_entry_view, name='marks_entry'),
    path('summary/', views.academic_summary_view, name='academic_summary'),
    path('progress/', views.progress_view, name='progress'),
    
    # Student Academic Hub URLs
    path('hub/', student_views.student_academic_hub, name='student_hub'),
    path('select-courses/', student_views.select_courses, name='select_courses'),
    path('simulate/', student_views.simulate_marks, name='simulate_marks'),
    path('simulation-preview/', student_views.simulation_preview, name='simulation_preview'),
    path('save-simulation/', student_views.save_simulation, name='save_simulation'),
    path('discard-simulation/', student_views.discard_simulation, name='discard_simulation'),
    path('drop-course/<int:registration_id>/', student_views.drop_selected_course, name='drop_course'),
]