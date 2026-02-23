from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import uuid



class User(AbstractUser):
    STUDENT = 'student'
    TEACHER = 'teacher'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (TEACHER, 'Teacher'),
        (ADMIN, 'Admin'),
    ]


    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    role = models.CharField(
        max_length=100, 
        choices=ROLE_CHOICES,
        default=STUDENT
    )
    is_premium = models.BooleanField(default=False)
    premium_expiry = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'User'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.email})"

    def promote_to_premium(self, days):
        self.is_premium = True
        now = timezone.now()
        if self.premium_expiry and self.premium_expiry > now:
            self.premium_expiry += timedelta(days=days)
        else:
            self.premium_expiry = now + timedelta(days=days)
        self.save()

    def demote_from_premium(self):
        self.is_premium = False
        self.premium_expiry = None
        self.save()

    def verify_user(self):
        self.is_verified = True
        self.save()

    def unverify_user(self):
        self.is_verified = False
        self.save()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'user_profile'

    def __str__(self):
        return f"Profile of {self.user.username}"


class UserSession(models.Model):
    """
    Track user sessions for analytics
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_token = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_at = models.DateTimeField(auto_now_add=True)
    logout_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_sessions'

    def logout(self):
        self.logout_at = timezone.now()
        self.is_active = False
        self.save()
