# Deploying to Google Cloud Platform

This guide explains how to deploy the Library Management System to Google Cloud Platform using Cloud Build and Cloud Run.

## Prerequisites

1. A Google Cloud Platform account
2. Google Cloud SDK installed locally
3. Enable the following APIs in your GCP project:
   - Cloud Build API
   - Cloud Run API
   - Container Registry API
   - Cloud SQL Admin API (if using Cloud SQL)

## Setup Steps

### 1. Create a Cloud Build Trigger

1. Go to the Cloud Build section in the Google Cloud Console
2. Navigate to Triggers and click "Create Trigger"
3. Connect your repository (GitHub, Bitbucket, or Cloud Source Repositories)
4. Configure the trigger settings:
   - Name: `library-management-system-build`
   - Event: Choose when to trigger the build (e.g., on push to main branch)
   - Source: Select your repository and branch
   - Configuration: Cloud Build configuration file (cloudbuild.yaml)
   - Click "Create"

### 2. Set up Environment Variables in Cloud Build

In the Cloud Build trigger settings, add the following substitution variables:

```
_SECRET_KEY: your-secure-secret-key
_ALLOWED_HOSTS: your-cloud-run-url.a.run.app,library.yourdomain.com
_DATABASE_URL: postgres://user:password@/dbname?host=/cloudsql/your-project:your-region:your-instance
_EMAIL_BACKEND: django.core.mail.backends.smtp.EmailBackend
_EMAIL_HOST: smtp.gmail.com
_EMAIL_PORT: 587
_EMAIL_USE_TLS: True
_EMAIL_HOST_USER: your-email@gmail.com
_EMAIL_HOST_PASSWORD: your-app-password
_DEFAULT_FROM_EMAIL: your-email@gmail.com
_LIBRARY_NAME: NTA Library
_LIBRARY_EMAIL: library@nta.edu
_LIBRARY_PHONE: +1234567890
_LIBRARY_ADDRESS: 123 Library Street, City, State 12345
_DAILY_FINE_AMOUNT: 1.00
_MAX_FINE_AMOUNT: 50.00
_BORROWING_PERIOD_DAYS: 14
_RESERVATION_PERIOD_DAYS: 7
_REDIS_URL: redis://10.0.0.1:6379/0
```

### 3. Set up a Database

#### Option 1: Cloud SQL (Recommended for Production)

1. Create a Cloud SQL instance (MySQL or PostgreSQL)
2. Configure the database and user
3. Update the `_DATABASE_URL` in your Cloud Build substitution variables

#### Option 2: Use SQLite (Not Recommended for Production)

If you want to use SQLite (not recommended for production), update the `_DATABASE_URL` to `sqlite:///db.sqlite3`

### 4. Deploy the Application

1. Push your code to the repository connected to the Cloud Build trigger
2. Cloud Build will automatically build and deploy your application to Cloud Run
3. You can also manually trigger a build from the Cloud Build console

### 5. Access Your Application

After deployment, you can access your application at the Cloud Run URL provided in the deployment output.

## Additional Configuration

### Static Files

Static files are served using WhiteNoise. For larger applications, consider using Cloud Storage:

1. Create a Cloud Storage bucket
2. Update the settings.py file to use Cloud Storage for static files
3. Add the necessary environment variables to cloudbuild.yaml

### Media Files

For user-uploaded files, it's recommended to use Cloud Storage:

1. Create a Cloud Storage bucket for media files
2. Update the settings.py file to use Cloud Storage for media files
3. Add the necessary environment variables to cloudbuild.yaml

### Scaling

Cloud Run automatically scales based on traffic. You can configure the minimum and maximum number of instances in the Cloud Run console.

## Troubleshooting

### Viewing Logs

1. Go to the Cloud Run section in the Google Cloud Console
2. Click on your service
3. Click on "Logs" to view the application logs

### Common Issues

1. **Database Connection Issues**: Ensure your Cloud SQL instance is properly configured and the connection string is correct
2. **Static Files Not Loading**: Check that WhiteNoise is properly configured
3. **Environment Variables**: Verify that all required environment variables are set in Cloud Build
4. **Build Failures with mysqlclient**: If you encounter errors related to mysqlclient installation (like missing pkg-config or MySQL libraries), this is already handled in the Dockerfile by installing the necessary system dependencies:
   ```
   default-libmysqlclient-dev
   pkg-config
   build-essential
   python3-dev
   ```
   If you still encounter issues, you may need to check the Cloud Build logs for specific errors

## Security Considerations

1. Store sensitive information (API keys, passwords) as Secret Manager secrets
2. Use HTTPS for all traffic
3. Regularly update dependencies
4. Implement proper authentication and authorization
5. Configure firewall rules to restrict access to your database