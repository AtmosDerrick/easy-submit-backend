from django.db import models
import uuid
from school.models import School, Department
from django.conf import settings

class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE, 
        null=False, 
        blank=False,
        related_name='courses'  
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='courses'  # Better naming: department.courses.all()
    )
    name = models.CharField(max_length=200)
    course_code = models.CharField(max_length=10, unique=True)  
    head_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True)
    academic_year = models.PositiveIntegerField(blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='courses_created', null=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['school', 'course_code']  # Course code should be unique within school
    
    def __str__(self):
        return f"{self.name} - {self.course_code}"
    
    def save(self, *args, **kwargs):
        # Ensure course_code is uppercase
        if self.course_code:
            self.course_code = self.course_code.upper()
        super().save(*args, **kwargs)


class Enrollment(models.Model): 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course, 
        on_delete=models.SET_NULL, 
        related_name='enrollments',
        null=True
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)  
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('dropped', 'Dropped'),
            ('pending', 'Pending'),
        ],
        default='active'
    )
    grade = models.CharField(
        max_length=2,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
            ('F', 'F'),
            ('P', 'Pass'),
            ('NP', 'No Pass'),
            ('I', 'Incomplete'),
            ('W', 'Withdrawn'),
        ],
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-enrollment_date']
        unique_together = ['course', 'user']  # Update this too
    
    def __str__(self):
        course_name = self.course.name if self.course else "[No Course]"
        user_name = self.user.username if self.user else "[No User]"
        return f"{user_name} - {course_name}"