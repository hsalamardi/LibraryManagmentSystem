#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Django Library Management System...${NC}"

# Function to wait for database
wait_for_db() {
    echo -e "${YELLOW}Waiting for database to be ready...${NC}"
    
    while ! python manage.py check --database default; do
        echo -e "${YELLOW}Database is unavailable - sleeping${NC}"
        sleep 2
    done
    
    echo -e "${GREEN}Database is ready!${NC}"
}

# Function to run migrations
run_migrations() {
    echo -e "${YELLOW}Running database migrations...${NC}"
    python manage.py migrate --noinput
    echo -e "${GREEN}Migrations completed!${NC}"
}

# Function to collect static files
collect_static() {
    # Check if static files are already collected (for production builds)
    if [ -d "/app/staticfiles" ] && [ "$(ls -A /app/staticfiles 2>/dev/null)" ]; then
        echo -e "${GREEN}Static files already collected, skipping...${NC}"
    else
        echo -e "${YELLOW}Collecting static files...${NC}"
        python manage.py collectstatic --noinput --clear
        echo -e "${GREEN}Static files collected!${NC}"
    fi
}

# Function to create superuser if it doesn't exist
create_superuser() {
    echo -e "${YELLOW}Checking for superuser...${NC}"
    
    # Use environment variables or defaults
    SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
    SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@library.com}
    SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-admin123}
    
    # Check if superuser already exists
    if python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())" | grep -q "True"; then
        echo -e "${GREEN}Superuser already exists${NC}"
    else
        echo -e "${YELLOW}Creating superuser: $SUPERUSER_USERNAME${NC}"
        # Use Django's built-in createsuperuser command with environment variables
        DJANGO_SUPERUSER_USERNAME=$SUPERUSER_USERNAME \
        DJANGO_SUPERUSER_EMAIL=$SUPERUSER_EMAIL \
        DJANGO_SUPERUSER_PASSWORD=$SUPERUSER_PASSWORD \
        python manage.py createsuperuser --noinput
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Superuser created successfully: $SUPERUSER_USERNAME${NC}"
        else
            echo -e "${RED}Failed to create superuser${NC}"
        fi
    fi
}

# Function to load initial data
load_initial_data() {
    echo -e "${YELLOW}Loading initial data...${NC}"
    
    # Check if there are any fixtures to load
    if [ -d "fixtures" ] && [ "$(ls -A fixtures)" ]; then
        python manage.py loaddata fixtures/*.json
        echo -e "${GREEN}Initial data loaded!${NC}"
    else
        echo -e "${YELLOW}No fixtures found, skipping initial data load${NC}"
    fi
}

# Function to check system
check_system() {
    echo -e "${YELLOW}Running system checks...${NC}"
    python manage.py check --deploy
    echo -e "${GREEN}System checks passed!${NC}"
}

# Main execution
case "$1" in
    web)
        wait_for_db
        run_migrations
        collect_static
        create_superuser
        load_initial_data
        check_system
        
        echo -e "${GREEN}Starting Gunicorn server...${NC}"
        exec gunicorn --bind 0.0.0.0:8000 \
                     --workers 3 \
                     --timeout 120 \
                     --max-requests 1000 \
                     --max-requests-jitter 100 \
                     --preload \
                     --access-logfile - \
                     --error-logfile - \
                     nta_library.wsgi:application
        ;;
    
    celery)
        wait_for_db
        echo -e "${GREEN}Starting Celery worker...${NC}"
        exec celery -A nta_library worker -l info --concurrency=2
        ;;
    
    celery-beat)
        wait_for_db
        echo -e "${GREEN}Starting Celery beat...${NC}"
        exec celery -A nta_library beat -l info
        ;;
    
    migrate)
        wait_for_db
        run_migrations
        ;;
    
    collectstatic)
        collect_static
        ;;
    
    createsuperuser)
        wait_for_db
        create_superuser
        ;;
    
    shell)
        wait_for_db
        exec python manage.py shell
        ;;
    
    test)
        wait_for_db
        echo -e "${YELLOW}Running tests...${NC}"
        exec python manage.py test
        ;;
    
    *)
        echo -e "${RED}Usage: $0 {web|celery|celery-beat|migrate|collectstatic|createsuperuser|shell|test}${NC}"
        echo -e "${YELLOW}Available commands:${NC}"
        echo -e "  web           - Start the Django web server with Gunicorn"
        echo -e "  celery        - Start Celery worker"
        echo -e "  celery-beat   - Start Celery beat scheduler"
        echo -e "  migrate       - Run database migrations only"
        echo -e "  collectstatic - Collect static files only"
        echo -e "  createsuperuser - Create superuser only"
        echo -e "  shell         - Start Django shell"
        echo -e "  test          - Run tests"
        exit 1
        ;;
esac