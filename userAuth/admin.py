from django.contrib import admin
from .models import BlacklistedToken, PasswordResetToken


admin.site.register(BlacklistedToken)
admin.site.register(PasswordResetToken)

# Register your models here.
