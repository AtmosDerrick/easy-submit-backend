from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from users.models import User
from .serializer import CustomTokenObtainPairSerializer, UserRegistrationSerializer

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings





class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
        
            if serializer.is_valid():
                user = serializer.save()
            
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
            
                response = Response({
                    'message': 'User registered successfully',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'phone_number': user.phone_number,
                    },
                    'access': access_token,  
                }, status=status.HTTP_201_CREATED)
                
                response.set_cookie(
                    'refresh_token',
                    value=refresh_token,
                    httponly=True,      
                    secure=True,        
                    samesite='Lax',    
                    max_age=60 * 60 * 24 * 7,  
                    path='/',        
                )
                
                return response
        
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



    
    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        tokens_data = serializer.validated_data
        refresh_token = tokens_data.get('refresh')
        access_token = tokens_data.get('access')
        user_data = tokens_data.get('user')
        
        
        response = Response({
            'message': 'Login successful',
            'access': access_token,
            'user': user_data
        }, status=status.HTTP_200_OK)
        
        response.set_cookie(
            'refresh_token',
            value=refresh_token,
            httponly=True,
            secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),  # Use settings value
            samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax'),  # Use settings value
            max_age=60 * 60 * 24 * 7,
            path='/',
        )
        
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        response = Response({'message': 'Logged out successfully'})
        
        response.delete_cookie('refresh_token', path='/')
        
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()  
            except Exception:
                pass
        
        return response


class VerifyTokenView(APIView):
  
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response({'valid': False}, status=status.HTTP_400_BAD_REQUEST)
        
        # Simple validation - in production, use proper JWT validation
        return Response({
            'valid': True,
            'message': 'Token is valid'
        })

class CustomTokenRefreshView(TokenRefreshView):
    
    def post(self, request, *args, **kwargs):

        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token not found'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        request.data['refresh'] = refresh_token
        
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            new_refresh_token = response.data.get('refresh')
            access_token = response.data.get('access')
            
            new_response = Response({
                'access': access_token,
                'message': 'Token refreshed successfully'
            })
            
            if new_refresh_token:
                new_response.set_cookie(
                    'refresh_token',
                    value=new_refresh_token,
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                    max_age=60 * 60 * 24 * 7,
                    path='/',
                )
            
            return new_response
        
        return response