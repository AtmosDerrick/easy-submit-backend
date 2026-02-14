# services.py
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import status
from rest_framework.response import Response
import uuid
from .models import Course, Enrollment
from .serializer import CourseSerializer

class CourseService:
    @staticmethod
    def search_course_service(course_id=None, course_code=None):
       
        if not course_id and not course_code:
            return None, Response({
                "detail": "Provide either 'course_id' or 'course_code' parameter."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        course = None
        
        if course_id:
            try:
                uuid.UUID(str(course_id))
                course = Course.objects.get(id=course_id)
            except (ValueError, ValidationError):
                return None, Response({
                    "detail": "Invalid course_id format."
                }, status=status.HTTP_400_BAD_REQUEST)
            except ObjectDoesNotExist:
                pass
        
        if not course and course_code:
            try:
                course = Course.objects.get(course_code__iexact=course_code.upper())
            except ObjectDoesNotExist:
                pass
        
        # FIXED: Check if course was found
        if not course:
            identifier = course_id or course_code
            return None, Response({
                "detail": f"Course '{identifier}' not found."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return course, None
    

    @staticmethod
    def check_user_course(user_id=None):
        if not user_id:
            return None, Response({
                "detail": "User ID is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_enrollments = Enrollment.objects.filter(
            user_id=user_id
        ).select_related('course')  
        
        if not user_enrollments.exists():
            return None, Response({
                "detail": "User is not enrolled in any course."
            }, status=status.HTTP_404_NOT_FOUND) 
        
        enrolled_courses = []
        for enrollment in user_enrollments:
            course_data = {
                'enrollment_id': str(enrollment.id),
                'course_id': str(enrollment.course.id) if enrollment.course else None,
                'course_name': enrollment.course.name if enrollment.course else 'Course Not Available',
                'course_code': enrollment.course.course_code if enrollment.course else 'N/A',
                'status': enrollment.status,
                'enrollment_date': enrollment.enrollment_date,
                'grade': enrollment.grade
            }
            enrolled_courses.append(course_data)
        
        response_data = {
            'user_id': user_id,
            'total_enrollments': user_enrollments.count(),
            'active_enrollments': user_enrollments.filter(status='active').count(),
            'enrolled_courses': enrolled_courses
        }
        
        return response_data, None

