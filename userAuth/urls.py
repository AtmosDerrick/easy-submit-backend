from django.urls import path
from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    LecturerRegisterView,
    LecturerTokenObtainPairView,
    LogoutView,
    CustomTokenRefreshView,
    VerifyTokenView,
)

urlpatterns = [
    # ── Student ───────────────────────────────────────────────
    path('register/',       RegisterView.as_view(),               name='student-register'),
    path('login/',          CustomTokenObtainPairView.as_view(),  name='student-login'),

    # ── Lecturer ──────────────────────────────────────────────
    path('lecturer/register/', LecturerRegisterView.as_view(),        name='lecturer-register'),
    path('lecturer/login/',    LecturerTokenObtainPairView.as_view(), name='lecturer-login'),

    # ── Shared ────────────────────────────────────────────────
    path('logout/',        LogoutView.as_view(),             name='logout'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('token/verify/',  VerifyTokenView.as_view(),        name='token-verify'),
]