from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Course, Enrollment
from .serializer import CourseSerializer, CourseCreateSerializer, EnrollmentSerializer
from .services import CourseService


def lecturer_only(user):
    return getattr(user, 'role', None) == 'teacher'


# ─── Create group ─────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createCourse(request):
    """
    Only lecturers can create a group.
    school and department are optional.
    The creating lecturer is set as head_id and created_by automatically.
    Returns the plain enrollment secret once — it is never stored in plain text.
    """
    if not lecturer_only(request.user):
        return Response(
            {"detail": "Only lecturers can create groups."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = CourseCreateSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    course = serializer.save()

    return Response({
        "message": "Group created successfully.",
        "course_code": course.course_code,
        # Plain secret shown once — student uses this to enroll
        "enrollment_secret": course._plain_secret,
        "created_by": str(request.user.id),
        "created_by_name": request.user.get_full_name() or request.user.username,
        "course": CourseSerializer(course).data,
    }, status=status.HTTP_201_CREATED)


# ─── Get groups created by the lecturer ──────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lecturer_courses(request):
    """
    Returns all groups the authenticated lecturer has created.
    """
    if not lecturer_only(request.user):
        return Response(
            {"detail": "Only lecturers can access this endpoint."},
            status=status.HTTP_403_FORBIDDEN
        )

    courses = Course.objects.filter(
        created_by=request.user
    ).prefetch_related('enrollments')

    serializer = CourseSerializer(courses, many=True)
    return Response({
        "message": "Groups retrieved successfully.",
        "data": {
            "total": courses.count(),
            "courses": serializer.data,
        }
    }, status=status.HTTP_200_OK)


# ─── Set admin (head) ─────────────────────────────────────────────────────────

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def set_admin(request):
    """
    Only the course creator or current head can transfer the head role.
    """
    course_id = request.data.get('course_id')
    head_id   = request.data.get('head_id')

    if not course_id:
        return Response({"detail": "course_id is required."}, status=status.HTTP_400_BAD_REQUEST)
    if not head_id:
        return Response({"detail": "head_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    course, error_response = CourseService.search_course_service(course_id=course_id)
    if error_response:
        return error_response

    # Only the creator or current head can transfer admin
    if str(request.user.id) not in [str(course.created_by_id), str(course.head_id_id)]:
        return Response(
            {"detail": "Only the group creator or current head can change the admin."},
            status=status.HTTP_403_FORBIDDEN
        )

    course.head_id_id = head_id
    course.save(update_fields=['head_id', 'updated_at'])

    return Response({
        "message": "Group head updated successfully.",
        "course_id": str(course.id),
        "course_name": course.name,
        "course_code": course.course_code,
        "head_id": str(course.head_id_id),
    }, status=status.HTTP_200_OK)


# ─── Search group ─────────────────────────────────────────────────────────────

@api_view(['GET'])
def search_course(request):
    course_id   = request.GET.get('course_id')
    course_code = request.GET.get('course_code')

    course, error_response = CourseService.search_course_service(
        course_id=course_id, course_code=course_code
    )
    if error_response:
        return error_response

    if not course:
        return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "message": "Group retrieved successfully.",
        "data": CourseSerializer(course).data,
    }, status=status.HTTP_200_OK)


# ─── Student enrollment ───────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enrollment(request, course_id):
    """
    Student enrolls in a group using the plain enrollment secret.
    The secret is compared against the stored hash — never logged or returned.
    """
    enrollment_key = request.data.get('enrollment_key')

    if not enrollment_key:
        return Response(
            {"detail": "Enrollment key is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    course, error_response = CourseService.search_course_service(course_id=course_id)
    if error_response:
        return error_response

    # Compare against hash — plain secret never touches the DB again
    if not course.check_secret(enrollment_key):
        return Response(
            {"detail": "Invalid enrollment key. Please check with your lecturer."},
            status=status.HTTP_403_FORBIDDEN
        )

    if Enrollment.objects.filter(course=course, user=request.user).exists():
        return Response(
            {"detail": "You are already enrolled in this group."},
            status=status.HTTP_400_BAD_REQUEST
        )

    new_enrollment = Enrollment.objects.create(
        course=course,
        user=request.user,
        status='active'
    )

    return Response({
        "message": "Successfully enrolled in the group.",
        "enrollment": EnrollmentSerializer(new_enrollment).data,
    }, status=status.HTTP_201_CREATED)


# ─── User enrollments ─────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_enrollments(request):
    enrollment_data, error_response = CourseService.check_user_course(
        user_id=str(request.user.id)
    )
    if error_response:
        return error_response

    return Response({
        "message": "User enrollment details retrieved successfully.",
        "data": enrollment_data,
    }, status=status.HTTP_200_OK)