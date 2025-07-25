"""
Tasks API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user_token
from ..models.task import Task, TaskComment, TaskStatus, TaskPriority
from ..models.project import Project, ProjectMember
from ..models.user import User

router = APIRouter()

# Pydantic schemas
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: int
    assignee_id: Optional[int] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    tags: List[str] = []
    depends_on: List[int] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    progress: Optional[float] = None
    tags: Optional[List[str]] = None
    depends_on: Optional[List[int]] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    project_id: int
    assignee_id: Optional[int]
    creator_id: int
    start_date: Optional[datetime]
    due_date: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: float
    progress: float
    depends_on: List[int]
    blocks: List[int]
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: int
    content: str
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

def check_project_access(project_id: int, user_id: int, db: Session):
    """Helper function to check if user has access to project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check access permissions
    is_owner = project.owner_id == user_id
    is_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first() is not None
    
    if not (is_owner or is_member or project.is_public):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    return project

@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Create a new task"""
    
    user_id = int(current_user["user_id"])
    
    # Check project access
    check_project_access(task_data.project_id, user_id, db)
    
    # Validate assignee if provided
    if task_data.assignee_id:
        assignee = db.query(User).filter(User.id == task_data.assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found"
            )
        
        # Check if assignee has access to project
        try:
            check_project_access(task_data.project_id, task_data.assignee_id, db)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee does not have access to this project"
            )
    
    # Create task
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        project_id=task_data.project_id,
        assignee_id=task_data.assignee_id,
        creator_id=user_id,
        priority=task_data.priority,
        start_date=task_data.start_date,
        due_date=task_data.due_date,
        estimated_hours=task_data.estimated_hours,
        tags=task_data.tags,
        depends_on=task_data.depends_on
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return TaskResponse.from_orm(db_task)

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    project_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assignee_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get tasks with filters"""
    
    user_id = int(current_user["user_id"])
    
    # Base query - tasks from projects user has access to
    query = db.query(Task).join(Project).join(ProjectMember).filter(
        or_(
            Project.owner_id == user_id,
            ProjectMember.user_id == user_id
        )
    )
    
    # Apply filters
    if project_id:
        check_project_access(project_id, user_id, db)
        query = query.filter(Task.project_id == project_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    if priority:
        query = query.filter(Task.priority == priority)
    
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    
    if search:
        query = query.filter(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%")
            )
        )
    
    # Execute query with pagination
    tasks = query.distinct().offset(skip).limit(limit).all()
    
    return [TaskResponse.from_orm(task) for task in tasks]

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get a specific task"""
    
    user_id = int(current_user["user_id"])
    
    # Get task and check project access
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    check_project_access(task.project_id, user_id, db)
    
    return TaskResponse.from_orm(task)

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Update a task"""
    
    user_id = int(current_user["user_id"])
    
    # Get task and check access
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    check_project_access(task.project_id, user_id, db)
    
    # Update task fields
    update_data = task_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    # Auto-set completed_at when status changes to completed
    if task_data.status == TaskStatus.COMPLETED and task.completed_at is None:
        task.completed_at = datetime.utcnow()
    elif task_data.status != TaskStatus.COMPLETED:
        task.completed_at = None
    
    db.commit()
    db.refresh(task)
    
    return TaskResponse.from_orm(task)

@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Delete a task"""
    
    user_id = int(current_user["user_id"])
    
    # Get task and check access
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    check_project_access(task.project_id, user_id, db)
    
    # Only creator or project owner can delete tasks
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if task.creator_id != user_id and project.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to delete this task"
        )
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}

@router.post("/{task_id}/comments", response_model=CommentResponse)
async def add_comment(
    task_id: int,
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Add a comment to a task"""
    
    user_id = int(current_user["user_id"])
    
    # Get task and check access
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    check_project_access(task.project_id, user_id, db)
    
    # Create comment
    db_comment = TaskComment(
        task_id=task_id,
        user_id=user_id,
        content=comment_data.content
    )
    
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    return CommentResponse.from_orm(db_comment)

@router.get("/{task_id}/comments", response_model=List[CommentResponse])
async def get_task_comments(
    task_id: int,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get comments for a task"""
    
    user_id = int(current_user["user_id"])
    
    # Get task and check access
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    check_project_access(task.project_id, user_id, db)
    
    # Get comments
    comments = db.query(TaskComment).filter(
        TaskComment.task_id == task_id
    ).order_by(TaskComment.created_at).all()
    
    return [CommentResponse.from_orm(comment) for comment in comments]