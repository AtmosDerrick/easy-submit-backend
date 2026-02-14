from django.urls import path
from . import views

urlpatterns = [
    path('create', views.createSchool, name='schools_create'),
    path('', views.get_schools, name='all_schools' ),
    path('<str:school_id>',views.school, name="school" ),

    path('department/create', views.create_department, name='department_create'),
    path('<str:department_id>', views.create_department, name='department_create'),


]
