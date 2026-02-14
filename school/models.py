import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings



class School(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(null=False, max_length=250 )
    school_code = models.CharField(max_length=20, unique=True, help_text="Unique school identifier")
    admin_ids = models.JSONField(
        default=list,
        help_text="Array of user IDs from User Service"
    )


    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)


    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Approval'),
        ('suspended', 'Suspended'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_verified = models.BooleanField(default=False)
    
    # School Details
    country = models.CharField(null=False, max_length=250 )
    region = models.CharField(null=False, max_length=250 )
    city = models.CharField(null=False, max_length=250 )
    established_year = models.PositiveIntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1800), MaxValueValidator(timezone.now().year)]
    )
    motto = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Logo & Media
    logo_url = models.URLField(blank=True, null=True)
    banner_url = models.URLField(blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete= models.DO_NOTHING,
        null=True, 
        blank=True,
        help_text="User ID from User Service who created this school"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields = ['school_code', 'id']),
            models.Index(fields=['status']),
            models.Index(fields=['city','country'])
        ]
        verbose_name = 'School'
    
    def __str__(self):
        return f"{self.name} ({self.school_code})"


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='departments')

    # department_code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    head_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
    
    def __str__(self):
        return f"{self.name} - {self.school.name}"
    
class SchoolAdmin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='admins')
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Permissions
    can_manage_courses = models.BooleanField(default=True)
    can_manage_students = models.BooleanField(default=True)
    can_manage_teachers = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['school', 'user_id']
        ordering = ['start_date']
        verbose_name = 'School Administrator'
        verbose_name_plural = 'School Administrators'
    
    def __str__(self):
        return f"{self.user_id} - {self.school.name}"
    
    


    

   





    