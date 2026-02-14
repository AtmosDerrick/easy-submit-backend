from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

from .views import RegisterView, CustomTokenObtainPairView, LogoutView, VerifyTokenView
from users.views import health_check

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check (required for API Gateway)
    path('health/', health_check, name='health-check'),
    
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify/', VerifyTokenView.as_view(), name='verify-token'),
    
    # Users
    path('users/', include('users.urls')),
]