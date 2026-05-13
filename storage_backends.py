from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class PrivateMediaStorage(S3Boto3Storage):
    """Storage for private media files using VPC endpoint"""
    location = settings.AWS_LOCATION
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False
    querystring_auth = True
    querystring_expire = settings.AWS_QUERYSTRING_EXPIRE

# Use this instead of DEFAULT_FILE_STORAGE if you need custom behavior
# DEFAULT_FILE_STORAGE = 'courses_service.storage_backends.PrivateMediaStorage'