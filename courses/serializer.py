from rest_framework import serializers
from .models import Course, Enrollment
import random
import string


class CourseSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    head_name = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'school', 'school_name', 'department', 'department_name',
            'name', 'course_code', 'head_id', 'head_name',
            'academic_year', 'description', 'member_count',
            'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'course_code', 'created_by']

    def get_head_name(self, obj):
        if obj.head_id:
            return obj.head_id.get_full_name() or obj.head_id.username
        return None

    def get_member_count(self, obj):
        return obj.enrollments.filter(status='active').count()


class CourseCreateSerializer(serializers.ModelSerializer):
    """
    Used when a lecturer creates a group.
    school, department, and head_id are all optional.
    course_code and created_by are set automatically.
    """
    class Meta:
        model = Course
        fields = ['school', 'department', 'name', 'academic_year', 'description']

    def create(self, validated_data):
        # Auto-generate a unique course code
        while True:
            letters = ''.join(random.choices(string.ascii_uppercase, k=3))
            numbers = ''.join(random.choices(string.digits, k=3))
            code = f"{letters}{numbers}"
            if not Course.objects.filter(course_code=code).exists():
                break

        # Generate plain secret, hash it, keep plain for the response
        plain_secret = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        hashed_secret = Course.hash_secret(plain_secret)

        request = self.context.get('request')
        lecturer = request.user if request else None

        course = Course.objects.create(
            **validated_data,
            course_code=code,
            course_code_secret=hashed_secret,
            head_id=lecturer,       # creator becomes the admin automatically
            created_by=lecturer,
        )

        # Stash plain secret temporarily so the view can return it once
        course._plain_secret = plain_secret
        return course


class EnrollmentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_code = serializers.CharField(source='course.course_code', read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'course_name', 'course_code',
            'user_id', 'enrollment_date', 'status', 'grade',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'enrollment_date']


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['course', 'user_id', 'status']

    def validate(self, data):
        if Enrollment.objects.filter(course=data['course'], user_id=data['user_id']).exists():
            raise serializers.ValidationError("User is already enrolled in this course.")
        return data