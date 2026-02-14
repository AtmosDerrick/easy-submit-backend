from rest_framework import serializers
from .models import User, UserProfile

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number')

    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        return user
    
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('bio', 'address', 'city', 'country', 'school')

    def update(self, instance, validated_data):
        profile = super().update(instance, validated_data)
        return profile

class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'is_verified', 'is_premium','premium_expiry', )