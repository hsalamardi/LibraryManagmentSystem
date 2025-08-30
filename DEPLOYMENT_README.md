# Library Management System Deployment Guide

## Local Docker Testing

Before deploying to Google Cloud Platform, you can test the Docker build locally:

### Windows

```
.\test_docker_build.bat
```

### Linux/Mac

```
chmod +x ./test_docker_build.sh
./test_docker_build.sh
```

This will build the Docker image and run it locally, exposing the application on http://localhost:8000.

## GCP Deployment

For detailed instructions on deploying to Google Cloud Platform, please refer to the [GCP Deployment Guide](./GCP_DEPLOYMENT.md).

## Common Issues

### mysqlclient Installation Errors

If you encounter errors related to mysqlclient installation (like missing pkg-config or MySQL libraries), this is already handled in the Dockerfile by installing the necessary system dependencies:

```
default-libmysqlclient-dev
pkg-config
build-essential
python3-dev
curl
```

### Package Availability Issues

Some packages may not be available in PyPI or may have different names. For example:

- `django-crispy-bootstrap5` has been replaced with `crispy-bootstrap5` in the requirements.txt file
- If you encounter similar issues with other packages, check the package name on PyPI or consider alternatives

### Database Migrations

The Cloud Build configuration includes a step to run database migrations automatically after deployment. If you need to run migrations manually, you can use the following command:

```
gcloud run jobs create migrate-db --image gcr.io/[PROJECT_ID]/[SERVICE_NAME]:[TAG] --command="python" --args="manage.py,migrate,--noinput" --region=[REGION]
```

### Environment Variables

Make sure all required environment variables are set in the Cloud Build trigger configuration or in the `.env` file for local testing.

**Important Note on Environment Variables Format:**

When setting environment variables in `cloudbuild.yaml`, use the correct format:
```yaml
--set-env-vars=KEY1=VALUE1,KEY2=VALUE2,KEY3=VALUE3
```

Do not use line breaks or spaces between variables. Make sure to escape special characters properly.

**Special Note for ALLOWED_HOSTS:**
Use space-separated domains instead of comma-separated to avoid parsing errors:
```yaml
_ALLOWED_HOSTS: 'domain1.com domain2.com'
```
Instead of:
```yaml
_ALLOWED_HOSTS: 'domain1.com,domain2.com'  # This will cause errors
```

**Special Characters in Values:**
For values containing spaces or special characters, replace spaces with underscores:
```yaml
_LIBRARY_ADDRESS: '123_Library_Street_City_State_12345'
```
Instead of:
```yaml
_LIBRARY_ADDRESS: '123 Library Street, City, State 12345'  # This will cause errors
```

## Monitoring and Logging

After deployment, you can monitor your application using Google Cloud Console:

1. Go to Cloud Run section
2. Click on your service
3. Click on "Logs" to view application logs
4. Click on "Metrics" to view performance metrics

## Scaling

Cloud Run automatically scales your application based on traffic. You can configure the minimum and maximum number of instances in the Cloud Run service settings.