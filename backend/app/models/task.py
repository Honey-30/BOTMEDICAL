"""
Task model for project management system
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from ..core.database import Base

class TaskStatus(str, Enum):
    """Task status enumeration"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    """Task priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Task(Base):
    """Task model for managing individual tasks within projects"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Task metadata
    status = Column(String(50), default=TaskStatus.TODO)
    priority = Column(String(50), default=TaskPriority.MEDIUM)
    
    # Project and assignment
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timeline
    start_date = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Work tracking
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, default=0.0)
    progress = Column(Float, default=0.0)  # Percentage completion
    
    # Dependencies
    depends_on = Column(JSON, default=[])  # List of task IDs this task depends on
    blocks = Column(JSON, default=[])  # List of task IDs this task blocks
    
    # AI-generated fields
    ai_priority_score = Column(Float, nullable=True)
    ai_risk_score = Column(Float, nullable=True)
    ai_suggestions = Column(JSON, default=[])
    
    # Task properties
    tags = Column(JSON, default=[])
    labels = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    
    # File attachments
    attachments = Column(JSON, default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks", foreign_keys=[assignee_id])
    creator = relationship("User", foreign_keys=[creator_id])
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task {self.title}>"
    
    def to_dict(self):
        """Convert task to dictionary for API responses"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "project_id": self.project_id,
            "assignee_id": self.assignee_id,
            "creator_id": self.creator_id,
            "start_date": self.start_date,
            "due_date": self.due_date,
            "completed_at": self.completed_at,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "progress": self.progress,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "ai_priority_score": self.ai_priority_score,
            "ai_risk_score": self.ai_risk_score,
            "tags": self.tags,
            "labels": self.labels,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class TaskComment(Base):
    """Comments on tasks for collaboration"""
    __tablename__ = "task_comments"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="comments")
    user = relationship("User")
    
    def __repr__(self):
        return f"<TaskComment task_id={self.task_id} user_id={self.user_id}>"