"""
User model for project management system
Adapted from existing BOTMEDICAL user model
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from ..core.database import Base

class UserRole(str, Enum):
    """User roles in the system"""
    USER = "user"
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    TEAM_LEAD = "team_lead"

class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    timezone = Column(String(50), default="UTC")
    
    # Authentication
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(50), default=UserRole.USER)
    
    # GitHub OAuth
    github_id = Column(String(100), unique=True, nullable=True)
    github_username = Column(String(100), nullable=True)
    
    # Settings
    preferences = Column(JSON, default={})
    notification_settings = Column(JSON, default={
        "email_notifications": True,
        "push_notifications": True,
        "project_updates": True,
        "task_assignments": True,
        "deadlines": True
    })
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    owned_projects = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")
    project_memberships = relationship("ProjectMember", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "location": self.location,
            "timezone": self.timezone,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "github_username": self.github_username,
            "created_at": self.created_at,
            "last_login": self.last_login
        }