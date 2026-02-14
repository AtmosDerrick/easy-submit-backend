
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('school/', include('school.urls')),
    path('courses/',include('courses.urls')),
    path('health/', include('users.urls')),
    path('auth/', include('userAuth.urls')),
    path('users/', include('users.urls')),
]
