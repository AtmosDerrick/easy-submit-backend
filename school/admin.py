from django.contrib import admin
from .models import School, Department,SchoolAdmin

# Register your models here.
admin.site.register(School)
admin.site.register(SchoolAdmin)
admin.site.register(Department)

