#!/usr/bin/env python
"""
Setup script for NTA Library Management System
This script creates a Django superuser from environment variables.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nta_library.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.core.management.base import CommandError
from dotenv import load_dotenv

def main():
    """Main setup function"""
    print("🚀 NTA Library Management System - Admin Setup")
    print("=" * 50)
    
    # Load environment variables
    env_file = project_dir / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from {env_file}")
    else:
        print(f"⚠️  No .env file found at {env_file}")
        print("Please create a .env file with the following variables:")
        print("- DJANGO_SUPERUSER_USERNAME")
        print("- DJANGO_SUPERUSER_EMAIL")
        print("- DJANGO_SUPERUSER_PASSWORD")
        return 1
    
    # Check required environment variables
    required_vars = [
        'DJANGO_SUPERUSER_USERNAME',
        'DJANGO_SUPERUSER_EMAIL', 
        'DJANGO_SUPERUSER_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please add them to your .env file.")
        return 1
    
    print("✅ All required environment variables found")
    
    try:
        # Run migrations first
        print("\n📦 Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Database migrations completed")
        
        # Create superuser
        print("\n👤 Creating Django superuser...")
        execute_from_command_line(['manage.py', 'create_superuser_from_env', '--force'])
        
        print("\n🎉 Setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Run: python manage.py runserver")
        print("2. Open: http://127.0.0.1:8000/admin/")
        print("3. Login with the credentials shown above")
        
        return 0
        
    except CommandError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())