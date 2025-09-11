# Docker Deployment Guide

This guide explains how to deploy the Library Management System using Docker and Docker Compose with external .env file mounting.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- External drive or secure location for .env file
- At least 2GB RAM available for containers

## Important: Static Files Fix

**✅ Static files (images, CSS, JS) are now automatically handled during the Docker build process.**

This deployment includes a permanent fix for static file serving:
- Static files are collected during `docker build`
- No manual intervention required
- Works automatically in production
- See `STATIC_FILES_FIX.md` for technical details

## Quick Start

### 1. Prepare Environment File

1. Copy the template to your external drive:
   ```bash
   cp .env.docker.template /path/to/external/drive/.env
   ```

2. Edit the .env file with your actual values:
   ```bash
   nano /path/to/external/drive/.env
   ```

3. Update the docker-compose.yaml file with the correct path:
   ```yaml
   volumes:
     - /path/to/external/drive/.env:/app/.env:ro
   ```

### 2. Build and Start Services

```bash
# Build the application
docker-compose build

# Start basic services (web + database + redis)
docker-compose up -d

# Or start with all services including nginx
docker-compose --profile production up -d

# Or start with celery workers
docker-compose --profile celery up -d
```

### 3. Initialize the Application

The application will automatically:
- Wait for database to be ready
- Run database migrations
- Collect static files
- Create a default superuser (admin/admin123)
- Load initial data if fixtures exist

### 4. Access the Application

- **Web Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin (admin/admin123 by default)
- **With Nginx**: http://localhost (port 80)

**Note**: A Django superuser is automatically created during container startup using the environment variables. The default credentials are:
- Username: `admin`
- Email: `admin@ntalibrary.edu`
- Password: `admin123`

You can customize these by modifying the environment variables in your configuration.

## Configuration Profiles

### Basic Profile (Default)
Includes: Django web app, MySQL database, Redis
```bash
docker-compose up -d
```

### Production Profile
Includes: Basic + Nginx reverse proxy
```bash
docker-compose --profile production up -d
```

### Celery Profile
Includes: Basic + Celery worker and beat scheduler
```bash
docker-compose --profile celery up -d
```

### Full Profile
Includes: All services
```bash
docker-compose --profile production --profile celery up -d
```

## Environment Variables

### Required Variables
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql://db_user:password@db:3306/database
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

### Database Variables
```env
MYSQL_DATABASE=database
MYSQL_USER=db_user
MYSQL_PASSWORD=password
MYSQL_ROOT_PASSWORD=password
```

### Email Configuration
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Django Admin Superuser
```env
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@ntalibrary.edu
DJANGO_SUPERUSER_PASSWORD=admin123
```

## Volume Management

### Persistent Data
- `db_data`: MySQL database files
- `redis_data`: Redis persistence
- `media_data`: Uploaded files (book covers, profile pics)
- `static_data`: Static files (CSS, JS, images)
- `logs_data`: Application logs

### Backup Volumes
```bash
# Backup database
docker-compose exec db mysqldump -u root -p database > backup.sql

# Backup media files
docker run --rm -v library_media_data:/data -v $(pwd):/backup alpine tar czf /backup/media_backup.tar.gz -C /data .
```

### Restore Volumes
```bash
# Restore database
docker-compose exec -T db mysql -u root -p database < backup.sql

# Restore media files
docker run --rm -v library_media_data:/data -v $(pwd):/backup alpine tar xzf /backup/media_backup.tar.gz -C /data
```

## Management Commands

### Application Management
```bash
# Run migrations
docker-compose exec web docker-entrypoint.sh migrate

# Create superuser
docker-compose exec web docker-entrypoint.sh createsuperuser

# Collect static files
docker-compose exec web docker-entrypoint.sh collectstatic

# Django shell
docker-compose exec web docker-entrypoint.sh shell

# Run tests
docker-compose exec web docker-entrypoint.sh test
```

### Container Management
```bash
# View logs
docker-compose logs -f web
docker-compose logs -f db

# Restart services
docker-compose restart web

# Scale web workers
docker-compose up -d --scale web=3

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Security Considerations

### External .env File
- Store .env file on encrypted external drive
- Set proper file permissions (600)
- Never commit .env to version control
- Regularly rotate secrets

### Container Security
- Application runs as non-root user
- Read-only .env file mounting
- Network isolation with custom bridge
- Health checks for all services

### Production Security
```env
# Enable in production
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Monitoring and Logging

### Health Checks
```bash
# Check service health
docker-compose ps

# View health check logs
docker inspect --format='{{.State.Health}}' library_web
```

### Log Management
```bash
# View application logs
docker-compose exec web tail -f /app/logs/library.log

# View all container logs
docker-compose logs -f

# Export logs
docker-compose logs > deployment.log
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check database status
   docker-compose exec db mysqladmin ping -h localhost
   
   # Reset database
   docker-compose down
   docker volume rm library_db_data
   docker-compose up -d
   ```

2. **Permission Denied on .env**
   ```bash
   # Fix file permissions
   chmod 600 /path/to/external/drive/.env
   chown $(whoami) /path/to/external/drive/.env
   ```

3. **Static Files Not Loading**
   ```bash
   # Recollect static files
   docker-compose exec web docker-entrypoint.sh collectstatic
   ```

4. **Memory Issues**
   ```bash
   # Check resource usage
   docker stats
   
   # Increase memory limits in docker-compose.yaml
   deploy:
     resources:
       limits:
         memory: 1G
   ```

### Debug Mode
```bash
# Run with debug output
docker-compose up --build

# Access container shell
docker-compose exec web bash

# Check environment variables
docker-compose exec web env | grep DJANGO
```

## Performance Optimization

### Production Tuning
```yaml
# In docker-compose.yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Database Optimization
```bash
# Add to docker-compose.yaml under db service
command: >
  --innodb-buffer-pool-size=256M
  --innodb-log-file-size=64M
  --max-connections=200
```

## Maintenance

### Regular Tasks
```bash
# Update containers
docker-compose pull
docker-compose up -d

# Clean up unused resources
docker system prune -f

# Update application
git pull
docker-compose build
docker-compose up -d
```

### Backup Schedule
```bash
# Add to crontab
0 2 * * * /path/to/backup-script.sh
```

## Support

For issues and questions:
1. Check the logs: `docker-compose logs`
2. Verify .env file configuration
3. Ensure external drive is mounted
4. Check Docker and Docker Compose versions
5. Review this documentation

---

**Note**: Always test the deployment in a staging environment before production use.