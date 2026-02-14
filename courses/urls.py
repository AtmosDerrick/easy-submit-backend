
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('create', views.createCourse, name='create_course'),
    path('search', views.search_course, name='search_course'),
    path('enroll/courseid/<str:course_id>', views.enrollment, name="enrollment"),
    path('enroll/usercourses', views.user_enrollments, name="user_enrollment" ),
    path('setadmin', views.set_admin, name="set_admin")
]
