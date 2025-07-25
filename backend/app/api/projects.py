"""
Projects API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user_token
from ..models.project import Project, ProjectMember, ProjectStatus, ProjectPriority
from ..models.user import User

router = APIRouter()

# Pydantic schemas
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    priority: ProjectPriority = ProjectPriority.MEDIUM
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    budget: Optional[float] = None
    estimated_hours: Optional[float] = None
    is_public: bool = False
    tags: List[str] = []

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    budget: Optional[float] = None
    estimated_hours: Optional[float] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    priority: str
    progress: float
    owner_id: int
    start_date: Optional[datetime]
    due_date: Optional[datetime]
    budget: Optional[float]
    estimated_hours: Optional[float]
    actual_hours: float
    is_public: bool
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ProjectMemberAdd(BaseModel):
    user_id: int
    role: str = "member"
    can_edit: bool = False
    can_delete: bool = False
    can_manage_members: bool = False

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    
    # Create project
    db_project = Project(
        name=project_data.name,
        description=project_data.description,
        priority=project_data.priority,
        start_date=project_data.start_date,
        due_date=project_data.due_date,
        budget=project_data.budget,
        estimated_hours=project_data.estimated_hours,
        is_public=project_data.is_public,
        tags=project_data.tags,
        owner_id=int(current_user["user_id"])
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Add owner as project admin
    db_membership = ProjectMember(
        project_id=db_project.id,
        user_id=int(current_user["user_id"]),
        role="admin",
        can_edit=True,
        can_delete=True,
        can_manage_members=True
    )
    db.add(db_membership)
    db.commit()
    
    return ProjectResponse.from_orm(db_project)

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[ProjectStatus] = None,
    priority: Optional[ProjectPriority] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get projects for current user"""
    
    user_id = int(current_user["user_id"])
    
    # Base query - projects owned by user or where user is a member
    query = db.query(Project).join(ProjectMember).filter(
        or_(
            Project.owner_id == user_id,
            ProjectMember.user_id == user_id
        )
    )
    
    # Apply filters
    if status:
        query = query.filter(Project.status == status)
    
    if priority:
        query = query.filter(Project.priority == priority)
    
    if search:
        query = query.filter(
            or_(
                Project.name.ilike(f"%{search}%"),
                Project.description.ilike(f"%{search}%")
            )
        )
    
    # Execute query with pagination
    projects = query.distinct().offset(skip).limit(limit).all()
    
    return [ProjectResponse.from_orm(project) for project in projects]

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get a specific project"""
    
    user_id = int(current_user["user_id"])
    
    # Check if user has access to this project
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
    
    return ProjectResponse.from_orm(project)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Update a project"""
    
    user_id = int(current_user["user_id"])
    
    # Get project and check permissions
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user can edit
    is_owner = project.owner_id == user_id
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    can_edit = is_owner or (member and member.can_edit)
    
    if not can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to edit this project"
        )
    
    # Update project fields
    update_data = project_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse.from_orm(project)

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Delete a project"""
    
    user_id = int(current_user["user_id"])
    
    # Get project and check permissions
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Only owner or members with delete permission can delete
    is_owner = project.owner_id == user_id
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    can_delete = is_owner or (member and member.can_delete)
    
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to delete this project"
        )
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}

@router.post("/{project_id}/members")
async def add_project_member(
    project_id: int,
    member_data: ProjectMemberAdd,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Add a member to the project"""
    
    user_id = int(current_user["user_id"])
    
    # Check project exists and user has permission
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions to manage members
    is_owner = project.owner_id == user_id
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    can_manage = is_owner or (member and member.can_manage_members)
    
    if not can_manage:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to manage project members"
        )
    
    # Check if user to add exists
    user_to_add = db.query(User).filter(User.id == member_data.user_id).first()
    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already a member
    existing_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == member_data.user_id
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this project"
        )
    
    # Add member
    db_member = ProjectMember(
        project_id=project_id,
        user_id=member_data.user_id,
        role=member_data.role,
        can_edit=member_data.can_edit,
        can_delete=member_data.can_delete,
        can_manage_members=member_data.can_manage_members
    )
    
    db.add(db_member)
    db.commit()
    
    return {"message": "Member added successfully"}

@router.get("/{project_id}/members")
async def get_project_members(
    project_id: int,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get project members"""
    
    user_id = int(current_user["user_id"])
    
    # Check access to project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access
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
    
    # Get members
    members = db.query(ProjectMember, User).join(User).filter(
        ProjectMember.project_id == project_id
    ).all()
    
    return [
        {
            "user_id": member.ProjectMember.user_id,
            "username": member.User.username,
            "full_name": member.User.full_name,
            "role": member.ProjectMember.role,
            "joined_at": member.ProjectMember.joined_at
        }
        for member in members
    ]