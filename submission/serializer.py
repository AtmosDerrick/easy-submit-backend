# serializers.py
from rest_framework import serializers
from .models import Submission, SubmissionReview


class SubmissionReviewSerializer(serializers.ModelSerializer):
    lecturer_name = serializers.CharField(source='lecturer.get_full_name', read_only=True)

    class Meta:
        model = SubmissionReview
        fields = [
            'id', 'lecturer', 'lecturer_name', 'comments',
            'feedback_file', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'lecturer', 'created_at', 'updated_at']


class SubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_code = serializers.CharField(source='course.course_code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviews = SubmissionReviewSerializer(many=True, read_only=True)
    latest_review = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            'id', 'course', 'course_name', 'course_code',
            'student', 'student_name', 'student_email',
            'version', 'status', 'status_display',
            'plagiarism_score', 'ai_score',
            'file', 'file_name', 'file_size', 'file_type',
            'submitted_at', 'updated_at',
            'reviews', 'latest_review'
        ]
        read_only_fields = [
            'id', 'plagiarism_score', 'ai_score',
            'submitted_at', 'updated_at', 'version'
        ]

    def get_latest_review(self, obj):
        latest = obj.reviews.first()
        return SubmissionReviewSerializer(latest).data if latest else None


class SubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['course', 'file']  # Remove file_name, file_size, file_type

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request else None

        if user:
            pending_exists = Submission.objects.filter(
                student=user,
                course=data['course'],
                status__in=[Submission.Status.PENDING, Submission.Status.UNDER_REVIEW]
            ).exists()

            if pending_exists:
                raise serializers.ValidationError(
                    "You already have a pending or under-review submission for this course."
                )

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        # Extract file metadata automatically
        uploaded_file = validated_data['file']
        file_name = uploaded_file.name
        file_size = uploaded_file.size
        file_type = uploaded_file.content_type  # e.g. 'application/pdf'

        latest = Submission.objects.filter(
            student=user,
            course=validated_data['course']
        ).order_by('-version').first()

        version = (latest.version + 1) if latest else 1

        submission = Submission.objects.create(
            student=user,
            version=version,
            status=Submission.Status.PENDING,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            **validated_data
        )

        return submission

class SubmissionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['file', 'file_name', 'file_size', 'file_type']

    def validate(self, data):
        if self.instance.status != Submission.Status.CHANGES_REQUIRED:
            raise serializers.ValidationError(
                "Can only update submissions that require changes."
            )
        return data

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.status = Submission.Status.PENDING
        instance.plagiarism_score = None
        instance.ai_score = None
        instance.save()
        return instance


class LecturerReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionReview
        fields = ['comments', 'feedback_file', 'status']

    def validate_status(self, value):
        submission = self.context['submission']
        current = submission.status

        allowed_transitions = {
            Submission.Status.PENDING: [
                Submission.Status.UNDER_REVIEW,
                Submission.Status.REJECTED,
            ],
            Submission.Status.UNDER_REVIEW: [
                Submission.Status.APPROVED,
                Submission.Status.CHANGES_REQUIRED,
                Submission.Status.REJECTED,
            ],
            Submission.Status.CHANGES_REQUIRED: [
                Submission.Status.APPROVED,
                Submission.Status.REJECTED,
            ],
        }

        allowed = allowed_transitions.get(current, [])
        if value not in allowed:
            allowed_labels = [s.label for s in allowed]
            raise serializers.ValidationError(
                f"Cannot transition from '{current}' to '{value}'. "
                f"Allowed transitions: {allowed_labels}"
            )
        return value

    def create(self, validated_data):
        submission = self.context['submission']
        request = self.context['request']

        review = SubmissionReview.objects.create(
            submission=submission,
            lecturer=request.user,
            **validated_data
        )

        submission.status = validated_data['status']
        submission.save(update_fields=['status', 'updated_at'])

        return review


class SubmissionListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # FIX: BooleanField with source='reviews.exists' does not work — use SerializerMethodField
    has_review = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            'id', 'student_name', 'course_name', 'version',
            'status', 'status_display', 'plagiarism_score', 'ai_score',
            'submitted_at', 'has_review'
        ]

    def get_has_review(self, obj):
        return obj.reviews.exists()