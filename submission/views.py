from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django_q.tasks import async_task
from courses.models import Course

from .models import Submission, SubmissionReview
from .serializer import (
    SubmissionCreateSerializer,
    SubmissionSerializer,
    SubmissionListSerializer,
    LecturerSubmissionDetailSerializer,
    LecturerReviewCreateSerializer,
)


def student_only(user):
    return getattr(user, 'role', None) == 'student'

def lecturer_only(user):
    return getattr(user, 'role', None) == 'teacher'


# ─── Student views ────────────────────────────────────────────────────────────

class SubmissionCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        if not student_only(request.user):
            return Response(
                {"detail": "Only students can submit assignments."},
                status=status.HTTP_403_FORBIDDEN
            )

        course_id = request.data.get('course')
        if course_id:
            Submission.objects.filter(
                student=request.user,
                course_id=course_id,
                is_draft=True,
            ).delete()

        serializer = SubmissionCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        submission = serializer.save()

        async_task(
            'submission.tasks.score_submission',
            str(submission.id),
            task_name=f"score-{submission.id}",
        )

        response_serializer = SubmissionSerializer(submission, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class SubmissionDetailView(APIView):
    """Student polls this until scores are non-null."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        submission = get_object_or_404(Submission, pk=pk, student=request.user)
        serializer = SubmissionSerializer(submission, context={'request': request})
        return Response(serializer.data)


class SubmissionConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        if not student_only(request.user):
            return Response(
                {"detail": "Only students can confirm submissions."},
                status=status.HTTP_403_FORBIDDEN
            )

        submission = get_object_or_404(
            Submission, pk=pk, student=request.user, is_draft=True,
        )

        if submission.plagiarism_score is None or submission.ai_score is None:
            return Response(
                {"detail": "Scoring is still in progress. Please wait and try again."},
                status=status.HTTP_409_CONFLICT,
            )

        submission.is_draft = False
        submission.status = Submission.Status.UNDER_REVIEW   # use the enum, not a raw string
        submission.save(update_fields=['is_draft', 'status', 'updated_at'])       
        

        serializer = SubmissionSerializer(submission, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmissionWithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, *args, **kwargs):
        if not student_only(request.user):
            return Response(
                {"detail": "Only students can withdraw submissions."},
                status=status.HTTP_403_FORBIDDEN
            )

        submission = get_object_or_404(
            Submission, pk=pk, student=request.user, is_draft=True,
        )
        submission.delete()
        return Response(
            {"detail": "Draft submission withdrawn successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class AllUserSubmissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not student_only(request.user):
            return Response(
                {"detail": "Only students can view their submissions."},
                status=status.HTTP_403_FORBIDDEN
            )

        submissions = Submission.objects.filter(
            student=request.user,
            is_draft=False,
        ).select_related('course')

        serializer = SubmissionListSerializer(submissions, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# ─── Lecturer views ───────────────────────────────────────────────────────────

class LecturerGroupSubmissionsView(APIView):
    """
    GET /submissions/group/<course_id>/
    All confirmed submissions for a group the lecturer heads.
    Optional: ?status=  ?student=
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id, *args, **kwargs):
        if not lecturer_only(request.user):
            return Response(
                {"detail": "Only lecturers can view group submissions."},
                status=status.HTTP_403_FORBIDDEN
            )

        group = get_object_or_404(Course, pk=course_id, head_id=request.user)

        submissions = Submission.objects.filter(
            course=group,
            is_draft=False,
        ).select_related('student', 'course').prefetch_related('reviews')

        status_filter = request.query_params.get('status')
        if status_filter:
            submissions = submissions.filter(status=status_filter)

        student_filter = request.query_params.get('student')
        if student_filter:
            submissions = submissions.filter(student__id=student_filter)

        serializer = SubmissionListSerializer(
            submissions, many=True, context={'request': request}
        )

        return Response({
            "group": {
                "id":            str(group.id),
                "name":          group.name,
                "course_code":   group.course_code,
                "academic_year": group.academic_year,
                "member_count":  group.enrollments.filter(status='active').count(),
            },
            "total":       submissions.count(),
            "submissions": serializer.data,
        }, status=status.HTTP_200_OK)


class LecturerSubmissionDetailView(APIView):
    """
    GET /submissions/<pk>/detail/
    Full detail for the review page — file URL, scores, all reviews.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        if not lecturer_only(request.user):
            return Response(
                {"detail": "Only lecturers can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN
            )

        submission = get_object_or_404(
            Submission,
            pk=pk,
            is_draft=False,
            course__head_id=request.user,
        )

        serializer = LecturerSubmissionDetailSerializer(
            submission, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class LecturerReviewView(APIView):
    """
    POST /submissions/<pk>/review/

    Lecturer submits a review with a decision, optional comments, and an
    optional feedback file attachment.

    Request body (multipart/form-data):
      - status        (required) — under_review | approved | changes_required | rejected
      - comments      (optional) — written feedback shown to the student
      - feedback_file (optional) — annotated file or document attachment

    Transition rules (validated in LecturerReviewCreateSerializer):
      pending          → under_review, rejected
      under_review     → approved, changes_required, rejected
      changes_required → approved, rejected

    Returns the full updated submission detail so the frontend
    can refresh the review panel in a single round trip.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk, *args, **kwargs):
        if not lecturer_only(request.user):
            return Response(
                {"detail": "Only lecturers can review submissions."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verify submission exists, is confirmed, and belongs to this lecturer's group
        submission = get_object_or_404(
            Submission,
            pk=pk,
            is_draft=False,
            course__head_id=request.user,
        )

        serializer = LecturerReviewCreateSerializer(
            data=request.data,
            context={
                'request':    request,
                'submission': submission,
            }
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Creates the SubmissionReview record and updates submission.status atomically
        serializer.save()

        # Refresh submission from DB to reflect updated status
        submission.refresh_from_db()

        # Return full updated detail — no second GET needed on the frontend
        response_serializer = LecturerSubmissionDetailSerializer(
            submission, context={'request': request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    
class StudentGroupHistoryView(APIView):
    """
    GET /submissions/history/<course_id>/

    Returns all confirmed submissions by the logged-in student
    for a specific group, with full review history per submission.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id, *args, **kwargs):
        if not student_only(request.user):
            return Response(
                {"detail": "Only students can access this."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verify the group exists and the student is enrolled
        group = get_object_or_404(Course, pk=course_id)

        submissions = (
            Submission.objects
            .filter(
                student=request.user,
                course=group,
                is_draft=False,
            )
            .select_related('course')
            .prefetch_related('reviews__lecturer')
            .order_by('-submitted_at')
        )

        serializer = SubmissionSerializer(
            submissions, many=True, context={'request': request}
        )

        return Response({
            "group": {
                "id":          str(group.id),
                "name":        group.name,
                "course_code": group.course_code,
            },
            "total":       submissions.count(),
            "submissions": serializer.data,
        }, status=status.HTTP_200_OK)