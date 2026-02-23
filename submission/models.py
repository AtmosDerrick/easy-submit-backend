# models.py
from django.db import models
import uuid
from courses.models import Course
from users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


def submission_upload_path(instance, filename):
    """Store files at: submissions/<course_code>/<student_id>/v<version>/<filename>"""
    return f"submissions/{instance.course.course_code}/{instance.student.id}/v{instance.version}/{filename}"


class Submission(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        UNDER_REVIEW = 'under_review', 'Under Review'
        CHANGES_REQUIRED = 'changes_required', 'Changes Required'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Local file storage
    file = models.FileField(upload_to=submission_upload_path)
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=100, help_text="MIME type")

    # Automated scores
    plagiarism_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True,
        help_text="Automated plagiarism detection score (0-100)"
    )
    ai_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True,
        help_text="Automated AI content detection score (0-100)"
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['student', 'course', 'version']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['student', 'course']),
        ]

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.course_code} (v{self.version})"


class SubmissionReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='reviews')
    lecturer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='lecturer_reviews',
        limit_choices_to={'role': 'lecturer'}
    )

    comments = models.TextField(blank=True)
    feedback_file = models.FileField(
        upload_to='submission_feedback/', blank=True, null=True,
        help_text="Optional feedback file"
    )

    # The status the lecturer is setting on the submission
    status = models.CharField(max_length=20, choices=Submission.Status.choices)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['submission', '-created_at']),
            models.Index(fields=['lecturer']),
        ]

    def __str__(self):
        lecturer_name = self.lecturer.get_full_name() if self.lecturer else "Unknown"
        return f"Review by {lecturer_name} for {self.submission}"