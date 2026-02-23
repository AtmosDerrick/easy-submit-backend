from django.contrib import admin
from .models import Submission, SubmissionReview

# Register your models here.
admin.site.register(Submission)
admin.site.register(SubmissionReview)