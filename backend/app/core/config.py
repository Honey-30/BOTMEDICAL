"""
Configuration module for Agentic AI Project Management Assistant
Adapted from existing config.py with FastAPI-specific settings
"""

import os
from typing import List
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings"""
    
    # App Configuration
    app_name: str = "Agentic AI Project Management Assistant"
    version: str = "1.0.0"
    debug: bool = False
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./project_management.db")
    
    # Supabase Configuration (for production)
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # AI Service Configuration
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    hugging_face_api_key: str = os.getenv("HUGGING_FACE_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")  # Fallback
    
    # GitHub OAuth Configuration
    github_client_id: str = os.getenv("GITHUB_CLIENT_ID", "")
    github_client_secret: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    
    # Email Configuration
    mail_server: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    mail_port: int = int(os.getenv("MAIL_PORT", "587"))
    mail_use_tls: bool = True
    mail_username: str = os.getenv("MAIL_USERNAME", "")
    mail_password: str = os.getenv("MAIL_PASSWORD", "")
    
    # CORS Configuration
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_folder: str = "uploads"
    allowed_extensions: List[str] = ["txt", "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx"]
    
    # AI Configuration
    confidence_threshold: float = 0.6
    max_tasks_per_project: int = 1000
    max_projects_per_user: int = 50
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if v.startswith("sqlite:"):
            return v
        elif v.startswith("postgresql:"):
            return v
        else:
            raise ValueError("Database URL must start with sqlite: or postgresql:")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Environment-specific configurations
class DevelopmentSettings(Settings):
    debug: bool = True
    database_url: str = "sqlite:///./dev_project_management.db"

class ProductionSettings(Settings):
    debug: bool = False
    # Use Supabase in production
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/projectdb")

class TestingSettings(Settings):
    debug: bool = True
    database_url: str = "sqlite:///:memory:"
    access_token_expire_minutes: int = 5  # Short for testing

# Configuration factory
def get_settings():
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()

# Global settings instance
settings = get_settings()