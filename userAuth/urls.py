from django.contrib import admin
from django.urls import path, include

from .views import RegisterView, CustomTokenObtainPairView, LogoutView, VerifyTokenView,CustomTokenRefreshView
from users.views import health_check

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify/', VerifyTokenView.as_view(), name='verify-token'),
]