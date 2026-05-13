# management/commands/list_s3_files.py
from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
from botocore.client import Config

class Command(BaseCommand):
    help = 'List all files in S3 bucket (including subfolders)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--prefix',
            type=str,
            help='Filter files by prefix (e.g., "media/")',
            default=None
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='List all files recursively',
        )
    
    def handle(self, *args, **options):
        if not getattr(settings, 'USE_S3', False):
            self.stdout.write(self.style.ERROR('S3 is not enabled'))
            return
        
        # Configure S3 client
        s3_params = {
            'region_name': settings.AWS_S3_REGION_NAME,
            'config': Config(signature_version='s3v4')
        }
        
        if hasattr(settings, 'AWS_S3_ENDPOINT_URL') and settings.AWS_S3_ENDPOINT_URL:
            s3_params['endpoint_url'] = settings.AWS_S3_ENDPOINT_URL
        
        if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID:
            s3_params['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
            s3_params['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
        
        s3 = boto3.client('s3', **s3_params)
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        
        self.stdout.write(f"\n🔍 Searching bucket: {bucket}")
        self.stdout.write(f"📍 Region: {settings.AWS_S3_REGION_NAME}")
        
        # Check if AWS_LOCATION is set (common for Django storages)
        aws_location = getattr(settings, 'AWS_LOCATION', None)
        if aws_location:
            self.stdout.write(f"📁 AWS_LOCATION: {aws_location}")
        
        # List files with pagination
        all_files = []
        continuation_token = None
        
        try:
            while True:
                list_kwargs = {'Bucket': bucket}
                if continuation_token:
                    list_kwargs['ContinuationToken'] = continuation_token
                
                # Add prefix filter if specified
                prefix = options.get('prefix')
                if prefix:
                    list_kwargs['Prefix'] = prefix
                elif options.get('all') and aws_location:
                    # List all files including those in subfolders
                    list_kwargs['Prefix'] = aws_location
                
                response = s3.list_objects_v2(**list_kwargs)
                
                if 'Contents' in response:
                    all_files.extend(response['Contents'])
                
                if response.get('IsTruncated'):
                    continuation_token = response.get('NextContinuationToken')
                else:
                    break
            
            if all_files:
                self.stdout.write(self.style.SUCCESS(f"\n✅ Found {len(all_files)} file(s):\n"))
                
                # Group by prefix
                files_by_prefix = {}
                for obj in all_files:
                    prefix = obj['Key'].split('/')[0] if '/' in obj['Key'] else 'root'
                    if prefix not in files_by_prefix:
                        files_by_prefix[prefix] = []
                    files_by_prefix[prefix].append(obj)
                
                # Display files
                for prefix, files in sorted(files_by_prefix.items()):
                    self.stdout.write(self.style.MIGRATE_HEADING(f"\n📁 {prefix}/"))
                    for obj in files:
                        self.stdout.write(f"  📄 {obj['Key']}")
                        self.stdout.write(f"     Size: {obj['Size']:,} bytes")
                        self.stdout.write(f"     Modified: {obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')}")
                        self.stdout.write("")
                
                # Show total size
                total_size = sum(obj['Size'] for obj in all_files)
                self.stdout.write(self.style.SUCCESS(f"\n📊 Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)"))
                
            else:
                self.stdout.write(self.style.WARNING('\n⚠️ No files found in bucket'))
                
                # Try to list without prefix to see if bucket has anything
                if not prefix and not options.get('all'):
                    self.stdout.write("\n💡 Tip: Try running with --all flag to search all folders:")
                    self.stdout.write(f"   python manage.py list_s3_files --all")
                    
                    # Also try to show bucket info
                    try:
                        # Check if bucket exists
                        s3.head_bucket(Bucket=bucket)
                        self.stdout.write(self.style.SUCCESS(f"\n✓ Bucket '{bucket}' exists and is accessible"))
                        
                        # Show bucket location
                        location = s3.get_bucket_location(Bucket=bucket)
                        self.stdout.write(f"📍 Bucket region: {location['LocationConstraint']}")
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Cannot access bucket: {e}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {e}'))
            import traceback
            traceback.print_exc()