"""
Notification model for project management system
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from ..core.database import Base

class NotificationType(str, Enum):
    """Notification type enumeration"""
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_OVERDUE = "task_overdue"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DEADLINE = "project_deadline"
    MEMBER_ADDED = "member_added"
    COMMENT_ADDED = "comment_added"
    AI_RISK_ALERT = "ai_risk_alert"
    AI_SUGGESTION = "ai_suggestion"
    SYSTEM_UPDATE = "system_update"

class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SLACK = "slack"
    WEBHOOK = "webhook"

class Notification(Base):
    """Notification model for user alerts and updates"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Recipients
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)
    
    # Related entities
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Delivery
    channels = Column(JSON, default=["in_app"])  # List of channels to send to
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    
    # Priority and scheduling
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    data = Column(JSON, default={})  # Additional data for the notification
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    project = relationship("Project", back_populates="notifications")
    task = relationship("Task")
    
    def __repr__(self):
        return f"<Notification {self.title} for user {self.user_id}>"
    
    def to_dict(self):
        """Convert notification to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "channels": self.channels,
            "is_read": self.is_read,
            "priority": self.priority,
            "scheduled_for": self.scheduled_for,
            "data": self.data,
            "created_at": self.created_at,
            "read_at": self.read_at
        }

class ChatSession(Base):
    """AI chat sessions for user interactions"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session metadata
    title = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Context
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    context_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession {self.id} for user {self.user_id}>"

class ChatMessage(Base):
    """Individual messages in chat sessions"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="user")  # user, assistant, system
    
    # AI processing
    intent = Column(String(100), nullable=True)
    entities = Column(JSON, default={})
    confidence = Column(Float, nullable=True)
    
    # Actions taken
    actions_performed = Column(JSON, default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage {self.id} in session {self.session_id}>"