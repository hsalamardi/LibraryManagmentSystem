# Django Admin Setup Guide

This guide explains how to configure and create Django admin credentials using environment variables for the NTA Library Management System.

## 🔧 Configuration

### Environment Variables

Add the following variables to your `.env` file:

```env
# Django Admin Superuser
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@ntalibrary.edu
DJANGO_SUPERUSER_PASSWORD=admin123
```

### Security Recommendations

⚠️ **Important Security Notes:**

1. **Change Default Password**: Always change the default password `admin123` to a strong, unique password
2. **Use Strong Passwords**: Use passwords with at least 12 characters, including uppercase, lowercase, numbers, and symbols
3. **Keep .env Secure**: Never commit your `.env` file to version control
4. **Production Settings**: Use different, more secure credentials for production environments

## 🚀 Quick Setup

### Method 1: Automated Setup Script

Run the automated setup script that handles everything:

```bash
python setup_admin.py
```

This script will:
- ✅ Load environment variables from `.env`
- ✅ Run database migrations
- ✅ Create/update the Django superuser
- ✅ Display login credentials

### Method 2: Manual Management Command

Alternatively, use the Django management command directly:

```bash
# Create new superuser (fails if user exists)
python manage.py create_superuser_from_env

# Force update existing superuser
python manage.py create_superuser_from_env --force
```

## 📋 Step-by-Step Setup

### 1. Configure Environment Variables

Create or update your `.env` file:

```bash
# Copy from example
cp .env.example .env

# Edit the file and set your admin credentials
# DJANGO_SUPERUSER_USERNAME=your_admin_username
# DJANGO_SUPERUSER_EMAIL=your_admin@email.com
# DJANGO_SUPERUSER_PASSWORD=your_secure_password
```

### 2. Run Database Migrations

```bash
python manage.py migrate
```

### 3. Create Admin User

```bash
python manage.py create_superuser_from_env
```

### 4. Start the Server

```bash
python manage.py runserver
```

### 5. Access Admin Panel

Open your browser and navigate to:
- **URL**: http://127.0.0.1:8000/admin/
- **Username**: (from your .env file)
- **Password**: (from your .env file)

## 🔄 Updating Admin Credentials

To update existing admin credentials:

1. Update the environment variables in your `.env` file
2. Run the command with `--force` flag:

```bash
python manage.py create_superuser_from_env --force
```

## 🛠️ Troubleshooting

### Common Issues

**Error: Environment variable is required**
- Ensure all required variables are set in your `.env` file
- Check for typos in variable names

**Error: User already exists**
- Use the `--force` flag to update existing users
- Or use a different username

**Error: No .env file found**
- Create a `.env` file in the project root
- Copy from `.env.example` and customize

### Verification

To verify your setup:

1. Check if the user was created:
   ```bash
   python manage.py shell
   >>> from django.contrib.auth import get_user_model
   >>> User = get_user_model()
   >>> User.objects.filter(is_superuser=True)
   ```

2. Test login at http://127.0.0.1:8000/admin/

## 🔐 Production Deployment

For production environments:

1. **Use Strong Credentials**:
   ```env
   DJANGO_SUPERUSER_USERNAME=library_admin
   DJANGO_SUPERUSER_EMAIL=admin@yourlibrary.org
   DJANGO_SUPERUSER_PASSWORD=VerySecurePassword123!
   ```

2. **Set Environment Variables on Server**:
   - Use your hosting platform's environment variable settings
   - Never store production credentials in files

3. **Run Setup on Deployment**:
   ```bash
   python setup_admin.py
   ```

## 📚 Available Commands

| Command | Description |
|---------|-------------|
| `python setup_admin.py` | Complete automated setup |
| `python manage.py create_superuser_from_env` | Create superuser from env vars |
| `python manage.py create_superuser_from_env --force` | Update existing superuser |

## 🎯 Benefits

- ✅ **Automated Setup**: No manual user creation needed
- ✅ **Environment-Based**: Credentials stored securely in environment variables
- ✅ **Deployment Ready**: Easy to deploy across different environments
- ✅ **Consistent**: Same setup process for development and production
- ✅ **Secure**: No hardcoded credentials in source code

---

**Need Help?** Check the main README.md or contact the development team.