from django.urls import path
from . import views

urlpatterns = [
    # Group management (lecturer only)
    path('create',                          views.createCourse,     name='create_course'),
    path('my-groups',                       views.lecturer_courses, name='lecturer_courses'),
    path('setadmin',                        views.set_admin,        name='set_admin'),

    # Discovery
    path('search',                          views.search_course,    name='search_course'),

    # Enrollment
    path('enroll/courseid/<str:course_id>', views.enrollment,       name='enrollment'),
    path('enroll/usercourses',              views.user_enrollments, name='user_enrollment'),
]