from rest_framework import serializers
from .models import Course, Enrollment
import random
import string
from .models import Course

class CourseSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'school', 'school_name', 'department', 'department_name', 
            'name', 'course_code', 'head_id', 'academic_year', 'description', 
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'course_code', 'created_by']


class CourseCreateSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(required=False, write_only=True) 
    
    class Meta:
        model = Course
        fields = ['school', 'department', 'name', 'academic_year', 'description', 'head_id', 'created_by']  
    def create(self, validated_data):
       
        # Generate course code if not provided
        if 'course_code' not in validated_data:    
            while True:
                letters_part = ''.join(random.choices(string.ascii_uppercase, k=3))
                numbers_part = ''.join(random.choices(string.digits, k=3))
                course_code = f"{letters_part}{numbers_part}"
                
                if not Course.objects.filter(course_code=course_code).exists():
                    validated_data['course_code'] = course_code
                    break
        
        return super().create(validated_data)

class EnrollmentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_code = serializers.CharField(source='course.course_code', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'course_name', 'course_code', 'user_id', 
            'enrollment_date', 'status', 'grade', 'created_at', 'updated_at' 
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'enrollment_date']

class EnrollmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment  
        fields = ['course', 'user_id', 'status',]
        
    def validate(self, data):
        if Enrollment.objects.filter(course=data['course'], user_id=data['user_id']).exists():
            raise serializers.ValidationError("User is already enrolled in this course.")
        return data