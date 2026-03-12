from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Course, Enrollment
from .serializer import CourseSerializer, CourseCreateSerializer, EnrollmentSerializer, EnrollmentCreateSerializer
from .services import CourseService
import random
import string






@api_view(['POST'])
def createCourse(request):
    try:
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        def generate_course_secret(length=6):
            """Generate a random alphanumeric string of specified length"""
            characters = string.ascii_uppercase + string.digits
            return ''.join(random.choices(characters, k=length))
        
        course_secret = generate_course_secret()
        
        mutable_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        mutable_data['course_code_secret'] = course_secret
        
        serializer = CourseCreateSerializer(data=mutable_data, context={'request': request})

        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save the course
        newCourse = serializer.save()
        
        return Response({
            "message": "Course created successfully",
            "course_code": newCourse.course_code,
            "course_secret": course_secret,  # Return the generated secret
            "created_by": user.id,
            "created_by_name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "course": CourseSerializer(newCourse).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            "detail": "An error occurred while creating the course",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['PATCH'])
def set_admin(request):
    try:
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        course_id = request.data.get('course_id')
        head_id = request.data.get('head_id')
        
        if not course_id:
            return Response({
                "detail": "Course ID is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not head_id:
            return Response({
                "detail": "Head ID is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        course, error_response = CourseService.search_course_service(course_id=course_id)
        
        if error_response:
            return error_response
        
        # permision = only set by created by and head_id
        course.head_id = head_id
        course.save()
        
        return Response({
            "message": "Course head updated successfully",
            "course_id": str(course.id),
            "course_name": course.name,
            "course_code": course.course_code,
            "head_id": course.head_id,
            "updated_at": course.updated_at
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "detail": "An error occurred while setting admin to course",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def search_course(request):
    
    try:
        course_id = request.GET.get('course_id')
        course_code = request.GET.get('course_code')

        course, error_response = CourseService.search_course_service(course_id=course_id, course_code=course_code)

        if error_response:
            return error_response
        
        if not course:
            return Response({
                "detail": "Course not found."
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CourseSerializer(course)
        return Response({
            "message": "Course retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "detail": "An error occurred while getting the course.",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def enrollment(request, course_id):
    try:
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        enrollment_key = request.data.get('enrollment_key')
        
        if not enrollment_key:
            return Response({
                "detail": "Enrollment key is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        course, error_response = CourseService.search_course_service(course_id=course_id)
        
        if error_response:
            return error_response
        
        print(course.course_code_secret,"diff", enrollment_key)  # Debugging line
        
        if course.course_code_secret != enrollment_key:  
            return Response({
                "detail": "Invalid enrollment key. Please check with your instructor."
            }, status=status.HTTP_403_FORBIDDEN)
        
        if Enrollment.objects.filter(course=course, user=user).exists():
            return Response({
                "detail": "You are already enrolled in this course."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        new_enrollment = Enrollment.objects.create(
            course=course,
            user=user,
            status='active'
        )
        
        return Response({
            "message": "Successfully enrolled in the course",
            "enrollment": EnrollmentSerializer(new_enrollment).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"Enrollment error: {str(e)}")  # For debugging
        return Response({
            "detail": "An error occurred while enrolling in this course.",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def user_enrollments(request):
    try:
        user = request.user
        print(user, "user")
        
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )  

        user_id = str(user.id)
      
        enrollment_data, error_response = CourseService.check_user_course(
            user_id=user_id
        )
        
        if error_response:
            return error_response
        
        return Response({
            "message": "User enrollment details retrieved successfully",
            "data": enrollment_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "detail": "An error occurred while checking user enrollment",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)