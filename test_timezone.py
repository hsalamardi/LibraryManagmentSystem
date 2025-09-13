import os
import django
from django.conf import settings
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nta_library.settings')
django.setup()

print(timezone.now())