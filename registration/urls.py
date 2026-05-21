from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    path('catalog/', views.course_catalog_view, name='course_catalog'),
    path('register/<int:course_id>/', views.register_course, name='register_course'),
    path('my-courses/', views.my_courses_view, name='my_courses'),
    path('drop/<int:registration_id>/', views.drop_course, name='drop_course'),
]