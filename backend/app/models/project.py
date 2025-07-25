"""
Project model for project management system
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from ..core.database import Base

class ProjectStatus(str, Enum):
    """Project status enumeration"""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ProjectPriority(str, Enum):
    """Project priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Project(Base):
    """Project model for managing projects and their properties"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Project metadata
    status = Column(String(50), default=ProjectStatus.PLANNING)
    priority = Column(String(50), default=ProjectPriority.MEDIUM)
    progress = Column(Float, default=0.0)  # Percentage completion
    
    # Ownership and collaboration
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timeline
    start_date = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Budget and resources
    budget = Column(Float, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, default=0.0)
    
    # Project settings
    is_public = Column(Boolean, default=False)
    allow_external_collaborators = Column(Boolean, default=False)
    
    # AI and automation settings
    ai_enabled = Column(Boolean, default=True)
    auto_prioritization = Column(Boolean, default=True)
    risk_monitoring = Column(Boolean, default=True)
    
    # Metadata
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="owned_projects", foreign_keys=[owner_id])
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="project")
    
    def __repr__(self):
        return f"<Project {self.name}>"
    
    def to_dict(self):
        """Convert project to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "progress": self.progress,
            "owner_id": self.owner_id,
            "start_date": self.start_date,
            "due_date": self.due_date,
            "completed_at": self.completed_at,
            "budget": self.budget,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "is_public": self.is_public,
            "ai_enabled": self.ai_enabled,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class ProjectMember(Base):
    """Association table for project members with roles"""
    __tablename__ = "project_members"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Member role in project
    role = Column(String(50), default="member")  # member, manager, admin
    
    # Permissions
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_manage_members = Column(Boolean, default=False)
    
    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")
    
    def __repr__(self):
        return f"<ProjectMember project_id={self.project_id} user_id={self.user_id}>"