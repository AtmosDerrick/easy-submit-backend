from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes

from django.shortcuts import get_object_or_404

from .models import User, UserProfile
from .serializer import  UserUpdateSerializer, ProfileUpdateSerializer, PublicUserSerializer
from userAuth.serializer import UserSerializer


class UserDetailView(generics.RetrieveUpdateAPIView):
   
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UpdateProfileView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request):
        user = request.user
        
        # Update user data
        user_serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        
        # Update profile data
        profile_serializer = ProfileUpdateSerializer(user.profile, data=request.data, partial=True)
        if profile_serializer.is_valid():
            profile_serializer.save()
        
        if user_serializer.is_valid() or profile_serializer.is_valid():
            # Return updated user
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_200_OK
            )
        
        # Combine errors
        errors = {}
        if user_serializer.errors:
            errors.update(user_serializer.errors)
        if profile_serializer.errors:
            errors.update(profile_serializer.errors)
        
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    """
    List all users (admin only)
    """
    queryset = User.objects.all()
    serializer_class = PublicUserSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = None


class GetUserByUsernameView(APIView):
    """
    Get public user data by username
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        serializer = PublicUserSerializer(user)
        return Response(serializer.data)


class GetUserByIdView(APIView):
    """
    Get public user data by id
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, id):
        user = get_object_or_404(User, id=id)
        serializer = PublicUserSerializer(user)
        return Response(serializer.data)


class SearchUsersView(generics.ListAPIView):
    """
    Search users by username or email
    """
    serializer_class = PublicUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if query:
            return User.objects.filter(
                username__icontains=query
            ) | User.objects.filter(
                email__icontains=query
            )
        return User.objects.none()


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """
    Health check endpoint for API Gateway
    """
    return Response({
        'status': 'healthy',
        'service': 'user-service',
        'version': '1.0.0',
        'database': 'connected' if User.objects.exists() else 'empty',
    })


class DeleteAccountView(APIView):
    """
    Delete user account
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request):
        user = request.user
        user.delete()
        
        return Response({
            'message': 'Account deleted successfully'
        }, status=status.HTTP_200_OK)