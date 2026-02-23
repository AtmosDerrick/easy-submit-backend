# views.py
import random
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from .models import Submission
from .serializer import SubmissionCreateSerializer, SubmissionSerializer


def simulate_automated_scores(submission: Submission):
    """
    Simulate plagiarism and AI detection scores with random values.
    Replace this with real Celery tasks / external API calls later.
    """
    submission.plagiarism_score = round(random.uniform(0, 100), 2)
    submission.ai_score = round(random.uniform(0, 100), 2)
    submission.save(update_fields=['plagiarism_score', 'ai_score'])


class SubmissionCreateView(APIView):
    """
    POST /submissions/
    Students submit a file for a course.
    - Only users with role='student' are allowed.
    - File is stored locally via Django's FileField.
    - Plagiarism and AI scores are simulated after creation.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Required for file upload

    def post(self, request, *args, **kwargs):
        # Role guard — only students may submit
        if getattr(request.user, 'role', None) != 'student':
            return Response(
                {"detail": "Only students can submit assignments."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = SubmissionCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        submission = serializer.save()

        # Simulate automated scoring (replace with async task in production)
        simulate_automated_scores(submission)

        # Return full submission detail
        response_serializer = SubmissionSerializer(submission, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)