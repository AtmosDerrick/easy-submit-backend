from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

from users.models import User
from .serializer import (
    CustomTokenObtainPairSerializer,
    LecturerRegistrationSerializer,
    LecturerTokenObtainPairSerializer,
    UserRegistrationSerializer,
)



# ─── Helpers ─────────────────────────────────────────────────────────────────

def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Attach the httpOnly refresh cookie — used by both register and login views."""
    response.set_cookie(
        'refresh_token',
        value=refresh_token,
        httponly=True,
        secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
        samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax'),
        max_age=60 * 60 * 24 * 7,
        path='/',
    )



class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        response = Response({
            'message': 'Student registered successfully.',
            'user': {
                'id':           user.id,
                'username':     user.username,
                'email':        user.email,
                'role':         user.role,
                'phone_number': user.phone_number,
            },
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

        set_refresh_cookie(response, str(refresh))
        return response


class CustomTokenObtainPairView(TokenObtainPairView):
    """Student login — blocks teacher/admin accounts."""
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Block non-students from the student login endpoint
        if data['user']['role'] != User.STUDENT:
            return Response(
                {'error': 'This login endpoint is for students only. Please use the lecturer login.'},
                status=status.HTTP_403_FORBIDDEN
            )

        response = Response({
            'message': 'Login successful.',
            'access':  data['access'],
            'user':    data['user'],
        }, status=status.HTTP_200_OK)

        set_refresh_cookie(response, data['refresh'])
        return response


# ─── Lecturer auth ────────────────────────────────────────────────────────────

class LecturerRegisterView(APIView):
    """
    POST /auth/lecturer/register/
    Creates a teacher-role account.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LecturerRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        response = Response({
            'message': 'Lecturer registered successfully.',
            'user': {
                'id':           user.id,
                'username':     user.username,
                'email':        user.email,
                'role':         user.role,
                'phone_number': user.phone_number,
            },
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

        set_refresh_cookie(response, str(refresh))
        return response


class LecturerTokenObtainPairView(TokenObtainPairView):
    """
    POST /auth/lecturer/login/
    Same flow as student login but enforces role='teacher'.
    Non-teacher accounts receive a 400 with a clear message.
    """
    serializer_class = LecturerTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        response = Response({
            'message': 'Lecturer login successful.',
            'access':  data['access'],
            'user':    data['user'],
        }, status=status.HTTP_200_OK)

        set_refresh_cookie(response, data['refresh'])
        return response


# ─── Shared ───────────────────────────────────────────────────────────────────

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        response = Response({'message': 'Logged out successfully.'})
        response.delete_cookie('refresh_token', path='/')

        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass

        return response


class CustomTokenRefreshView(TokenRefreshView):
    """
    POST /auth/token/refresh/
    Reads the refresh token from the httpOnly cookie — no body needed.
    """
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token not found.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        request.data['refresh'] = refresh_token

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token      = response.data.get('access')
            new_refresh_token = response.data.get('refresh')  # only present when ROTATE_REFRESH_TOKENS=True

            new_response = Response({
                'access':  access_token,
                'message': 'Token refreshed successfully.',
            })

            if new_refresh_token:
                set_refresh_cookie(new_response, new_refresh_token)

            return new_response

        return response


class VerifyTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'valid': False}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'valid': True, 'message': 'Token is valid.'})