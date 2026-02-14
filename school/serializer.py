from rest_framework import serializers
from .models import School, Department, SchoolAdmin

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = [
            'id', 'school_code', 'name',
            'email', 'phone', 'website',
             'city',  'country', 
            'status', 'is_verified',
            'established_year', 'motto', 'description',
            'logo_url', 'banner_url',
            'created_by', 'created_at', 'updated_at',
            
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

        def validate_email(self, value):
            if value:
                schools = School.objects.filter(email__iexact=value)
            if self.instance:
                schools = schools.exclude(pk=self.instance.pk)
            if schools.exists():
                raise serializers.ValidationError("A school with this email already exists")
            return value


class SchoolCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = [
             'school_code', 'name', 
            'email', 'phone', 'website',
             'city', 'country','region', 
            'established_year', 'motto', 'description'

        ]
        
class DepartmentSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    
    class Meta:
        model = Department
        fields = [
            'id', 'school', 'school_name', 'name',
            'description', 'head_id', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SchoolAdminSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    is_current = serializers.SerializerMethodField()
    
    class Meta:
        model = SchoolAdmin
        fields = [
            'id', 'school', 'school_name', 'user_id', 'role', 'is_active', 'start_date', 'end_date',
            'is_current', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_current(self, obj):
        return obj.is_current_admin()
    