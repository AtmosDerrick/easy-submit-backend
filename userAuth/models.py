from django.db import models
from django.conf import settings
from django.utils import timezone

class BlacklistedToken(models.Model):
    """
    Store blacklisted JWT tokens
    """
    token = models.TextField(unique=True)
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'blacklisted_tokens'
        indexes = [
            models.Index(fields=['expires_at']),
        ]
    
    def is_expired(self):
        return timezone.now() > self.expires_at


class PasswordResetToken(models.Model):
    """
    Password reset tokens
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
    
    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at