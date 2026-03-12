from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django_q.tasks import async_task

from .models import Submission
from .serializer import SubmissionCreateSerializer, SubmissionSerializer



def student_only(user):
    return getattr(user, 'role', None) == 'student'



class SubmissionCreateView(APIView):
    """
    Step 1 of the submission flow.

    - Creates a draft submission (is_draft=True)
    - Enqueues a background scoring task via Django-Q2
    - Returns immediately with null scores — client should poll until scores appear

    Scores are attached to the draft so when the student hits confirm,
    no recalculation happens — they confirm exactly what was scored.
    """
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

        # Enqueue scoring — the worker picks this up and saves scores to the DB.
        # The task receives a string ID because UUIDs aren't JSON-serializable by default.
        async_task(
            'submission.tasks.score_submission',
            str(submission.id),
            task_name=f"score-{submission.id}",
        )

        response_serializer = SubmissionSerializer(submission, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)



class SubmissionDetailView(APIView):
    """
    Returns the current state of a submission.
    Used by the client to poll for scores after the draft is created.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        submission = get_object_or_404(
            Submission,
            pk=pk,
            student=request.user,
        )
        serializer = SubmissionSerializer(submission, context={'request': request})
        return Response(serializer.data)



class SubmissionConfirmView(APIView):
    """
    Confirms a draft submission, making it visible to lecturers.
    Scores are already attached from the background task — nothing is recalculated.
    Blocked if scoring hasn't completed yet (scores still null).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        if not student_only(request.user):
            return Response(
                {"detail": "Only students can confirm submissions."},
                status=status.HTTP_403_FORBIDDEN
            )

        submission = get_object_or_404(
            Submission,
            pk=pk,
            student=request.user,
            is_draft=True,
        )

        # Guard: don't allow confirming before scoring has finished.
        # This prevents a submission landing in a lecturer's queue with null scores.
        if submission.plagiarism_score is None or submission.ai_score is None:
            return Response(
                {"detail": "Scoring is still in progress. Please wait and try again."},
                status=status.HTTP_409_CONFLICT,
            )

        submission.is_draft = False
        submission.save(update_fields=['is_draft', 'updated_at'])

        serializer = SubmissionSerializer(submission, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# DELETE /submissions/<id>/
# Step 2b — student withdraws draft before confirming.
# ---------------------------------------------------------------------------

class SubmissionWithdrawView(APIView):
    """
    Withdraws (deletes) a draft submission.
    If the scoring task hasn't run yet it will exit cleanly — the task
    checks for existence before doing any work.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, *args, **kwargs):
        if not student_only(request.user):
            return Response(
                {"detail": "Only students can withdraw submissions."},
                status=status.HTTP_403_FORBIDDEN
            )

        submission = get_object_or_404(
            Submission,
            pk=pk,
            student=request.user,
            is_draft=True,
        )

        submission.delete()
        return Response(
            {"detail": "Draft submission withdrawn successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )