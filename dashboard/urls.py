from django.urls import path
from . import views
from . import admin_views

app_name = 'dashboard'

urlpatterns = [
    # Student dashboard
    path('', views.home_view, name='home'),
    
    # Admin dashboard URLs
    path('admin/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/manage-students/', admin_views.manage_students, name='manage_students'),
    path('admin/edit-student/<int:student_id>/', admin_views.edit_student, name='edit_student'),
    path('admin/student/<int:student_id>/', admin_views.student_details, name='student_details'),
    path('admin/manage-registrations/', admin_views.manage_registrations, name='manage_registrations'),
    path('admin/approve-registration/<int:registration_id>/', admin_views.approve_registration, name='approve_registration'),
    path('admin/drop-registration/<int:registration_id>/', admin_views.admin_drop_course, name='admin_drop_course'),
    path('admin/bulk-assign/', admin_views.bulk_assign_programme, name='bulk_assign'),
    
    # Programme management URLs
    path('admin/manage-departments/', admin_views.manage_departments, name='manage_departments'),
    path('admin/manage-programmes/', admin_views.manage_programmes, name='manage_programmes'),
    path('admin/add-programme/', admin_views.add_programme, name='add_programme'),
    path('admin/programme/<int:programme_id>/', admin_views.programme_details, name='programme_details'),
    path('admin/edit-programme/<int:programme_id>/', admin_views.edit_programme, name='edit_programme'),
]