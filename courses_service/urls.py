
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('school/', include('school.urls')),
    path('courses/',include('courses.urls')),
    path('health/', include('users.urls')),
    path('auth/', include('userAuth.urls')),
    path('users/', include('users.urls')),
    path('submissions/', include('submission.urls'))
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
