#!/bin/bash
# Development helper script for Docker-based development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="southeast"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Show help
show_help() {
    cat << EOF
${GREEN}SouthEast Archers Development Helper${NC}

Usage: ./dev.sh [command]

Commands:
  ${BLUE}up${NC}              Start development environment
  ${BLUE}down${NC}            Stop development environment
  ${BLUE}restart${NC}         Restart development environment
  ${BLUE}build${NC}           Rebuild Docker images (add --no-cache for clean build)
  ${BLUE}logs${NC}            Show logs (add service name: logs web)
  ${BLUE}shell${NC}           Open shell in web container
  ${BLUE}manage${NC}          Run Django management command (e.g., ./dev.sh manage migrate)
  ${BLUE}migrate${NC}         Run database migrations
  ${BLUE}makemigrations${NC}  Create new migrations
  ${BLUE}createsuperuser${NC} Create Django superuser
  ${BLUE}test${NC}            Run tests
  ${BLUE}dbshell${NC}         Open database shell
  ${BLUE}install${NC}         Install new package with uv (e.g., ./dev.sh install requests)
  ${BLUE}tailwind${NC}        Run Tailwind command (e.g., ./dev.sh tailwind build)
  ${BLUE}clean${NC}           Stop and remove all containers, volumes, and images
  ${BLUE}status${NC}          Show status of containers
  ${BLUE}help${NC}            Show this help message

Examples:
  ./dev.sh up
  ./dev.sh logs web
  ./dev.sh manage createsuperuser
  ./dev.sh install django-debug-toolbar

EOF
}

# Start development environment
cmd_up() {
    check_docker
    print_info "Starting development environment..."
    docker-compose -f $COMPOSE_FILE up -d
    print_success "Development environment started!"
    print_info "Web application: http://localhost:8000"
    print_info "Run './dev.sh logs' to see logs"
}

# Stop development environment
cmd_down() {
    print_info "Stopping development environment..."
    docker-compose -f $COMPOSE_FILE down
    print_success "Development environment stopped!"
}

# Restart development environment
cmd_restart() {
    print_info "Restarting development environment..."
    docker-compose -f $COMPOSE_FILE restart
    print_success "Development environment restarted!"
}

# Rebuild images
cmd_build() {
    check_docker
    local NO_CACHE=""
    if [ "$1" = "--no-cache" ]; then
        NO_CACHE="--no-cache"
        print_info "Building Docker images without cache..."
    else
        print_info "Building Docker images..."
    fi
    docker-compose -f $COMPOSE_FILE build $NO_CACHE
    print_success "Docker images built successfully!"
}

# Show logs
cmd_logs() {
    if [ -z "$1" ]; then
        docker-compose -f $COMPOSE_FILE logs -f
    else
        docker-compose -f $COMPOSE_FILE logs -f "$@"
    fi
}

# Open shell in web container
cmd_shell() {
    print_info "Opening shell in web container..."
    docker-compose -f $COMPOSE_FILE exec web bash || docker-compose -f $COMPOSE_FILE exec web sh
}

# Run Django management command
cmd_manage() {
    if [ -z "$1" ]; then
        print_error "Please specify a management command"
        exit 1
    fi
    docker-compose -f $COMPOSE_FILE exec web python manage.py "$@"
}

# Run migrations
cmd_migrate() {
    print_info "Running database migrations..."
    docker-compose -f $COMPOSE_FILE exec web python manage.py migrate
    print_success "Migrations completed!"
}

# Create migrations
cmd_makemigrations() {
    print_info "Creating migrations..."
    docker-compose -f $COMPOSE_FILE exec web python manage.py makemigrations "$@"
}

# Create superuser
cmd_createsuperuser() {
    print_info "Creating superuser..."
    docker-compose -f $COMPOSE_FILE exec web python manage.py createsuperuser
}

# Run tests
cmd_test() {
    print_info "Running tests..."
    docker-compose -f $COMPOSE_FILE exec web pytest "$@"
}

# Open database shell
cmd_dbshell() {
    print_info "Opening database shell..."
    docker-compose -f $COMPOSE_FILE exec db mysql -uroot -p"${MYSQL_ROOT_PASSWORD:-devpassword}" "${DB_NAME:-southeast_archers}"
}

# Install package with uv
cmd_install() {
    if [ -z "$1" ]; then
        print_error "Please specify a package to install"
        exit 1
    fi
    print_info "Installing $@ with uv..."
    docker-compose -f $COMPOSE_FILE exec web uv add "$@"
    print_success "Package installed! Rebuilding container..."
    docker-compose -f $COMPOSE_FILE build web
    docker-compose -f $COMPOSE_FILE up -d web
}

# Run Tailwind command
cmd_tailwind() {
    if [ -z "$1" ]; then
        print_error "Please specify a Tailwind command"
        exit 1
    fi
    docker-compose -f $COMPOSE_FILE exec web python manage.py tailwind "$@"
}

# Clean everything
cmd_clean() {
    print_warning "This will remove all containers, volumes, and development images!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        docker-compose -f $COMPOSE_FILE down -v --rmi local
        print_success "Cleanup complete!"
    else
        print_info "Cleanup cancelled"
    fi
}

# Show status
cmd_status() {
    docker-compose -f $COMPOSE_FILE ps
}

# Main command dispatcher
case "${1:-help}" in
    up)
        cmd_up
        ;;
    down)
        cmd_down
        ;;
    restart)
        cmd_restart
        ;;
    build)
        shift
        cmd_build "$@"
        ;;
    logs)
        shift
        cmd_logs "$@"
        ;;
    shell)
        cmd_shell
        ;;
    manage)
        shift
        cmd_manage "$@"
        ;;
    migrate)
        cmd_migrate
        ;;
    makemigrations)
        shift
        cmd_makemigrations "$@"
        ;;
    createsuperuser)
        cmd_createsuperuser
        ;;
    test)
        shift
        cmd_test "$@"
        ;;
    dbshell)
        cmd_dbshell
        ;;
    install)
        shift
        cmd_install "$@"
        ;;
    tailwind)
        shift
        cmd_tailwind "$@"
        ;;
    clean)
        cmd_clean
        ;;
    status)
        cmd_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
