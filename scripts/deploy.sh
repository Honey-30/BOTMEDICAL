#!/bin/bash

# Production deployment script for AI Healthcare Chatbot
# This script handles deployment to various environments

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
APP_NAME="healthchatbot"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"
VERSION="${VERSION:-$(date +%Y%m%d-%H%M%S)}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if required environment files exist
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        log_warning ".env file not found, copying from .env.example"
        if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        else
            log_error ".env.example file not found"
            exit 1
        fi
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build production image
    docker build -t "${APP_NAME}:${VERSION}" \
                 -t "${APP_NAME}:latest" \
                 --target production .
    
    # Tag for registry if specified
    if [[ "$DOCKER_REGISTRY" != "localhost:5000" ]]; then
        docker tag "${APP_NAME}:${VERSION}" "${DOCKER_REGISTRY}/${APP_NAME}:${VERSION}"
        docker tag "${APP_NAME}:latest" "${DOCKER_REGISTRY}/${APP_NAME}:latest"
    fi
    
    log_success "Docker images built successfully"
}

# Push images to registry
push_images() {
    if [[ "$DOCKER_REGISTRY" == "localhost:5000" ]]; then
        log_info "Skipping image push (using local registry)"
        return
    fi
    
    log_info "Pushing images to registry..."
    
    docker push "${DOCKER_REGISTRY}/${APP_NAME}:${VERSION}"
    docker push "${DOCKER_REGISTRY}/${APP_NAME}:latest"
    
    log_success "Images pushed to registry"
}

# Deploy to development environment
deploy_development() {
    log_info "Deploying to development environment..."
    
    cd "$PROJECT_ROOT"
    
    # Stop existing containers
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
    
    # Pull latest images
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml pull
    
    # Start services
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    
    # Wait for services to be ready
    wait_for_services
    
    # Run database migrations
    run_migrations
    
    log_success "Development deployment completed"
}

# Deploy to staging environment
deploy_staging() {
    log_info "Deploying to staging environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create staging override file
    cat > docker-compose.staging.yml << EOF
version: '3.8'
services:
  app:
    image: ${DOCKER_REGISTRY}/${APP_NAME}:${VERSION}
    environment:
      - FLASK_ENV=staging
    ports:
      - "8000:5000"
EOF
    
    # Deploy to staging
    docker-compose -f docker-compose.yml -f docker-compose.staging.yml down
    docker-compose -f docker-compose.yml -f docker-compose.staging.yml pull
    docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
    
    wait_for_services
    run_migrations
    
    log_success "Staging deployment completed"
}

# Deploy to production environment
deploy_production() {
    log_info "Deploying to production environment..."
    
    # Additional checks for production
    if [[ -z "$PRODUCTION_CONFIRM" ]]; then
        read -p "Are you sure you want to deploy to PRODUCTION? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_info "Production deployment cancelled"
            exit 0
        fi
    fi
    
    cd "$PROJECT_ROOT"
    
    # Backup current deployment
    backup_production
    
    # Create production override file
    cat > docker-compose.prod.yml << EOF
version: '3.8'
services:
  app:
    image: ${DOCKER_REGISTRY}/${APP_NAME}:${VERSION}
    environment:
      - FLASK_ENV=production
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
EOF
    
    # Rolling deployment to production
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate
    
    wait_for_services
    run_migrations
    
    # Run health checks
    run_health_checks
    
    log_success "Production deployment completed"
}

# Wait for services to be ready
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for database
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose exec -T db pg_isready -U healthbot -d healthchatbot; then
            break
        fi
        
        log_info "Waiting for database... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Database failed to start"
        exit 1
    fi
    
    # Wait for Redis
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose exec -T redis redis-cli ping; then
            break
        fi
        
        log_info "Waiting for Redis... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    # Wait for application
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:5000/api/health 2>/dev/null; then
            break
        fi
        
        log_info "Waiting for application... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    log_success "All services are ready"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    docker-compose exec -T app flask db upgrade
    
    log_success "Database migrations completed"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # API health check
    if ! curl -f http://localhost:5000/api/health; then
        log_error "API health check failed"
        return 1
    fi
    
    # Database connectivity check
    if ! docker-compose exec -T app python -c "from app import db; db.engine.execute('SELECT 1')"; then
        log_error "Database connectivity check failed"
        return 1
    fi
    
    # Redis connectivity check
    if ! docker-compose exec -T app python -c "from app.utils.cache import cache; cache.set('health_check', 'ok'); assert cache.get('health_check') == 'ok'"; then
        log_error "Redis connectivity check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

# Backup production data
backup_production() {
    log_info "Creating production backup..."
    
    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup database
    docker-compose exec -T db pg_dump -U healthbot healthchatbot > "$backup_dir/database.sql"
    
    # Backup Redis data
    docker-compose exec -T redis redis-cli BGSAVE
    docker cp "$(docker-compose ps -q redis):/data/dump.rdb" "$backup_dir/redis.rdb"
    
    # Backup uploaded files
    if [[ -d "$PROJECT_ROOT/uploads" ]]; then
        cp -r "$PROJECT_ROOT/uploads" "$backup_dir/"
    fi
    
    # Create backup metadata
    cat > "$backup_dir/metadata.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "${VERSION}",
    "environment": "production",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
}
EOF
    
    log_success "Backup created at $backup_dir"
}

# Rollback deployment
rollback() {
    log_warning "Rolling back deployment..."
    
    # Get previous version from backup directory
    local latest_backup=$(ls -1 "$PROJECT_ROOT/backups" | tail -n 2 | head -n 1)
    
    if [[ -z "$latest_backup" ]]; then
        log_error "No backup found for rollback"
        exit 1
    fi
    
    log_info "Rolling back to backup: $latest_backup"
    
    # Stop current deployment
    docker-compose down
    
    # Restore database
    docker-compose up -d db
    sleep 10
    cat "$PROJECT_ROOT/backups/$latest_backup/database.sql" | docker-compose exec -T db psql -U healthbot healthchatbot
    
    # Restore Redis
    docker cp "$PROJECT_ROOT/backups/$latest_backup/redis.rdb" "$(docker-compose ps -q redis):/data/dump.rdb"
    docker-compose restart redis
    
    # Restore uploaded files
    if [[ -d "$PROJECT_ROOT/backups/$latest_backup/uploads" ]]; then
        rm -rf "$PROJECT_ROOT/uploads"
        cp -r "$PROJECT_ROOT/backups/$latest_backup/uploads" "$PROJECT_ROOT/"
    fi
    
    # Start previous version
    docker-compose up -d
    
    wait_for_services
    
    log_success "Rollback completed"
}

# Clean up old images and containers
cleanup() {
    log_info "Cleaning up old images and containers..."
    
    # Remove unused containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    # Remove old app images (keep latest 5)
    docker images "${APP_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}" | \
        grep -v latest | tail -n +6 | awk '{print $3}' | xargs -r docker rmi
    
    log_success "Cleanup completed"
}

# Main deployment function
main() {
    local environment="${1:-development}"
    local action="${2:-deploy}"
    
    case "$action" in
        "build")
            check_prerequisites
            build_images
            ;;
        "push")
            push_images
            ;;
        "deploy")
            check_prerequisites
            build_images
            
            case "$environment" in
                "development"|"dev")
                    deploy_development
                    ;;
                "staging"|"stage")
                    push_images
                    deploy_staging
                    ;;
                "production"|"prod")
                    push_images
                    deploy_production
                    ;;
                *)
                    log_error "Unknown environment: $environment"
                    exit 1
                    ;;
            esac
            ;;
        "rollback")
            rollback
            ;;
        "cleanup")
            cleanup
            ;;
        "health")
            run_health_checks
            ;;
        *)
            log_error "Unknown action: $action"
            echo "Usage: $0 [environment] [action]"
            echo "Environments: development, staging, production"
            echo "Actions: build, push, deploy, rollback, cleanup, health"
            exit 1
            ;;
    esac
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
