from django.db import models
import uuid
import hashlib
from school.models import School, Department
from django.conf import settings


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # School and department are optional — a lecturer can create a group
    # without belonging to a school/department structure
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='courses'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )

    name = models.CharField(max_length=200)
    course_code = models.CharField(max_length=10, unique=True)

    # Stored as SHA-256 hash — the plain secret is returned once at creation
    # and never stored or exposed again
    course_code_secret = models.CharField(max_length=256, default='', blank=True)

    # Set automatically to the creating lecturer — not supplied by the client
    head_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        null=True,
        related_name='headed_courses'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        related_name='courses_created',
        null=True
    )

    academic_year = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.course_code}"

    def save(self, *args, **kwargs):
        if self.course_code:
            self.course_code = self.course_code.upper()
        super().save(*args, **kwargs)

    @staticmethod
    def hash_secret(plain_secret: str) -> str:
        return hashlib.sha256(plain_secret.encode()).hexdigest()

    def check_secret(self, plain_secret: str) -> bool:
        return self.course_code_secret == self.hash_secret(plain_secret)


class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        related_name='enrollments',
        null=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
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
            ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('F', 'F'),
            ('P', 'Pass'), ('NP', 'No Pass'), ('I', 'Incomplete'), ('W', 'Withdrawn'),
        ],
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-enrollment_date']
        unique_together = ['course', 'user']

    def __str__(self):
        course_name = self.course.name if self.course else "[No Course]"
        return f"{self.user.username} - {course_name}"