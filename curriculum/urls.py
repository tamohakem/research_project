from django.urls import path
from . import views

app_name = 'curriculum'

urlpatterns = [
    path('courses/', views.course_list_view, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail_view, name='course_detail'),
]