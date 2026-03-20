# Add this to your existing submission/serializers.py
# alongside SubmissionSerializer, SubmissionListSerializer etc.

from rest_framework import serializers
from .models import Submission, SubmissionReview


# Add this to your existing submission/serializers.py
# alongside SubmissionSerializer, SubmissionListSerializer etc.

from rest_framework import serializers
from .models import Submission, SubmissionReview


class ReviewDetailSerializer(serializers.ModelSerializer):
    """Full review detail — used inside LecturerSubmissionDetailSerializer."""
    reviewer_name  = serializers.CharField(source='lecturer.get_full_name', read_only=True)
    reviewer_email = serializers.CharField(source='lecturer.email', read_only=True)
    feedback_file_url = serializers.SerializerMethodField()

    class Meta:
        model  = SubmissionReview
        fields = [
            'id',
            'reviewer_name',
            'reviewer_email',
            'comments',
            'feedback_file_url',  # absolute URL, null if no file attached
            'status',             # the status the reviewer set on the submission
            'created_at',
            'updated_at',
        ]

    def get_feedback_file_url(self, obj):
        if not obj.feedback_file:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.feedback_file.url) if request else obj.feedback_file.url


class LecturerSubmissionDetailSerializer(serializers.ModelSerializer):
    """
    Full detail serializer for the lecturer review view.
    Includes the absolute file URL so the frontend can pass it
    directly to DocxViewer without any extra transformation.
    """
    # Student info
    student_id    = serializers.CharField(source='student.id', read_only=True)
    student_name  = serializers.CharField(source='student.get_full_name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)

    # Group info
    course_id     = serializers.CharField(source='course.id', read_only=True)
    course_name   = serializers.CharField(source='course.name', read_only=True)
    course_code   = serializers.CharField(source='course.course_code', read_only=True)

    # Status
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # File — absolute URL, ready for DocxViewer
    file_url = serializers.SerializerMethodField()

    # Reviews — ordered latest first
    reviews = ReviewDetailSerializer(many=True, read_only=True)

    # Latest review shortcut
    latest_review = serializers.SerializerMethodField()

    class Meta:
        model  = Submission
        fields = [
            # Identity
            'id',
            'version',

            # Student
            'student_id',
            'student_name',
            'student_email',

            # Group
            'course_id',
            'course_name',
            'course_code',

            # File — pass file_url directly to DocxViewer
            'file_url',
            'file_name',
            'file_size',
            'file_type',

            # Integrity scores
            'plagiarism_score',
            'ai_score',

            # Status
            'status',
            'status_display',

            # Reviews
            'reviews',
            'latest_review',

            # Timestamps
            'submitted_at',
            'updated_at',
        ]

    def get_file_url(self, obj):
        """
        Returns the absolute URL to the submitted file.
        Pass this directly as the `fileUrl` prop on DocxViewer.
        """
        if not obj.file:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url

    def get_latest_review(self, obj):
        latest = obj.reviews.first()  # reviews ordered by -created_at
        if not latest:
            return None
        return ReviewDetailSerializer(latest, context=self.context).data