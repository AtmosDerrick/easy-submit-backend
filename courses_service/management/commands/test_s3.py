# courses_service/management/commands/test_s3.py
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import Content
from django.conf import settings
import sys

class Command(BaseCommand):
    help = 'Test S3 connectivity from private subnet'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up test files after testing',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*50)
        self.stdout.write("Testing S3 Configuration")
        self.stdout.write("="*50 + "\n")
        
        # Check if S3 is enabled
        if not settings.USE_S3:
            self.stdout.write(self.style.WARNING(
                "⚠️  S3 is not enabled (USE_S3=False)"
            ))
            self.stdout.write("Set USE_S3=True in your .env file to enable S3")
            return
        
        self.stdout.write(f"✓ S3 is enabled")
        self.stdout.write(f"✓ Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
        self.stdout.write(f"✓ Region: {settings.AWS_S3_REGION_NAME}")
        self.stdout.write(f"✓ Storage backend: {default_storage.__class__.__name__}")
        self.stdout.write("")
        
        # Test file operations
        test_file_name = 'test_vpc_endpoint.txt'
        test_content = Content(b"Hello from private subnet via VPC endpoint!")
        
        try:
            # Test 1: Upload
            self.stdout.write("📤 Testing upload...")
            saved_path = default_storage.save(test_file_name, test_content)
            self.stdout.write(self.style.SUCCESS(f"  ✓ Uploaded: {saved_path}"))
            
            # Test 2: Generate signed URL
            self.stdout.write("\n🔗 Testing signed URL generation...")
            signed_url = default_storage.url(saved_path)
            self.stdout.write(self.style.SUCCESS(f"  ✓ Signed URL generated"))
            self.stdout.write(f"  📎 URL (truncated): {signed_url[:150]}...")
            self.stdout.write(f"  ⏱️  Expires in: {settings.AWS_QUERYSTRING_EXPIRE} seconds")
            
            # Test 3: Check if file exists
            self.stdout.write("\n🔍 Testing file existence...")
            exists = default_storage.exists(saved_path)
            if exists:
                self.stdout.write(self.style.SUCCESS("  ✓ File exists in S3"))
            else:
                self.stdout.write(self.style.ERROR("  ✗ File not found in S3"))
            
            # Test 4: Get file size
            try:
                size = default_storage.size(saved_path)
                self.stdout.write(self.style.SUCCESS(f"  ✓ File size: {size} bytes"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠️  Could not get file size: {e}"))
            
            # Cleanup if requested
            if options['cleanup']:
                self.stdout.write("\n🧹 Cleaning up...")
                default_storage.delete(saved_path)
                self.stdout.write(self.style.SUCCESS("  ✓ Test file deleted"))
            
            self.stdout.write("\n" + "="*50)
            self.stdout.write(self.style.SUCCESS("✅ S3 IS WORKING CORRECTLY!"))
            self.stdout.write("="*50 + "\n")
            
        except Exception as e:
            self.stdout.write("\n" + "="*50)
            self.stdout.write(self.style.ERROR("❌ S3 CONNECTION FAILED!"))
            self.stdout.write("="*50)
            self.stdout.write(f"\nError details: {str(e)}")
            self.stdout.write("\nTroubleshooting tips:")
            self.stdout.write("1. Verify VPC endpoint is created and attached to private subnet route table")
            self.stdout.write("2. Check IAM role has S3 permissions")
            self.stdout.write("3. Verify bucket name is correct")
            self.stdout.write("4. Check if bucket exists and is accessible")
            self.stdout.write("5. Verify security group allows outbound HTTPS (if using interface endpoint)")
            sys.exit(1)