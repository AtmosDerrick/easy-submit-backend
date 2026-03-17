from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import password_validation, authenticate
from users.models import User, UserProfile


# ─── Registration ─────────────────────────────────────────────────────────────

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Student registration — role is locked to 'student'."""
    password  = serializers.CharField(write_only=True, required=True, validators=[password_validation.validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model  = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'phone_number')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', None),
            password=validated_data['password'],
            role=User.STUDENT,
        )
        UserProfile.objects.create(user=user)
        return user


class LecturerRegistrationSerializer(serializers.ModelSerializer):
    """
    Lecturer registration — role is locked to 'teacher'.
    Kept separate from student registration intentionally so the
    endpoint, validation rules, and response shape can diverge independently.
    """
    password  = serializers.CharField(write_only=True, required=True, validators=[password_validation.validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model  = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'phone_number')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', None),
            password=validated_data['password'],
            role=User.TEACHER,
        )
        UserProfile.objects.create(user=user)
        return user


# ─── Token ────────────────────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Shared login serializer for all roles.
    Embeds role in the JWT so the frontend can gate UI without an extra API call.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username']    = user.username
        token['email']       = user.email
        token['role']        = user.role
        token['is_premium']  = user.is_premium
        token['is_verified'] = user.is_verified
        return token

    def validate(self, attrs):
        username_or_email = attrs.get('username')
        password          = attrs.get('password')

        if not username_or_email or not password:
            raise serializers.ValidationError('Both username/email and password are required.')

        user = None
        if '@' in username_or_email:
            try:
                db_user = User.objects.get(email=username_or_email)
                user = authenticate(username=db_user.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(username=username_or_email, password=password)

        if user is None:
            raise serializers.ValidationError('Invalid credentials.')
        if not user.is_active:
            raise serializers.ValidationError('This account has been disabled.')

        refresh = self.get_token(user)

        return {
            'refresh': str(refresh),
            'access':  str(refresh.access_token),
            'user': {
                'id':           user.id,
                'username':     user.username,
                'email':        user.email,
                'role':         user.role,
                'first_name':   user.first_name,
                'last_name':    user.last_name,
                'is_premium':   user.is_premium,
                'is_verified':  user.is_verified,
                'phone_number': user.phone_number,
            }
        }


class LecturerTokenObtainPairSerializer(CustomTokenObtainPairSerializer):
    """
    Login serializer for the lecturer endpoint only.
    Reuses all shared logic but blocks non-teacher accounts so a student
    cannot authenticate via /auth/lecturer/login/.
    """
    def validate(self, attrs):
        data = super().validate(attrs)

        if data['user']['role'] != User.TEACHER:
            raise serializers.ValidationError(
                'This login endpoint is for lecturers only. '
                'Please use the student login.'
            )

        return data


# ─── Profile ─────────────────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UserProfile
        fields = '__all__'
        read_only_fields = ('user',)


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model  = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'role',
            'is_verified', 'is_premium', 'premium_expiry',
            'created_at', 'updated_at', 'profile'
        )
        read_only_fields = (
            'id', 'role', 'is_verified', 'is_premium',
            'premium_expiry', 'created_at', 'updated_at'
        )