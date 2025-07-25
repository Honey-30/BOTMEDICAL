"""
Analytics API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.security import get_current_user_token
from ..models.project import Project, ProjectMember
from ..models.task import Task, TaskStatus
from ..models.user import User

router = APIRouter()

# Pydantic schemas
class ProjectAnalytics(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    overdue_projects: int
    projects_by_status: Dict[str, int]
    projects_by_priority: Dict[str, int]

class TaskAnalytics(BaseModel):
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    tasks_by_status: Dict[str, int]
    tasks_by_priority: Dict[str, int]
    completion_rate: float

class ProductivityMetrics(BaseModel):
    tasks_completed_today: int
    tasks_completed_this_week: int
    tasks_completed_this_month: int
    average_completion_time: Optional[float]
    productivity_trend: str

class OverviewAnalytics(BaseModel):
    project_analytics: ProjectAnalytics
    task_analytics: TaskAnalytics
    productivity_metrics: ProductivityMetrics

@router.get("/overview", response_model=OverviewAnalytics)
async def get_overview_analytics(
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get overview analytics for the current user"""
    
    user_id = int(current_user["user_id"])
    
    # Get user's projects (owned or member)
    user_projects = db.query(Project).join(ProjectMember).filter(
        (Project.owner_id == user_id) | (ProjectMember.user_id == user_id)
    ).distinct().all()
    
    project_ids = [p.id for p in user_projects]
    
    # Project Analytics
    total_projects = len(user_projects)
    active_projects = len([p for p in user_projects if p.status == "active"])
    completed_projects = len([p for p in user_projects if p.status == "completed"])
    
    # Projects by status and priority
    projects_by_status = {}
    projects_by_priority = {}
    overdue_projects = 0
    
    for project in user_projects:
        # Status count
        projects_by_status[project.status] = projects_by_status.get(project.status, 0) + 1
        
        # Priority count
        projects_by_priority[project.priority] = projects_by_priority.get(project.priority, 0) + 1
        
        # Overdue check
        if project.due_date and project.due_date < datetime.utcnow() and project.status != "completed":
            overdue_projects += 1
    
    # Task Analytics
    if project_ids:
        tasks = db.query(Task).filter(Task.project_id.in_(project_ids)).all()
    else:
        tasks = []
    
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
    in_progress_tasks = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
    
    # Tasks by status and priority
    tasks_by_status = {}
    tasks_by_priority = {}
    overdue_tasks = 0
    
    for task in tasks:
        # Status count
        tasks_by_status[task.status] = tasks_by_status.get(task.status, 0) + 1
        
        # Priority count
        tasks_by_priority[task.priority] = tasks_by_priority.get(task.priority, 0) + 1
        
        # Overdue check
        if task.due_date and task.due_date < datetime.utcnow() and task.status != TaskStatus.COMPLETED:
            overdue_tasks += 1
    
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Productivity Metrics
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    tasks_completed_today = len([
        t for t in tasks 
        if t.status == TaskStatus.COMPLETED and t.completed_at and t.completed_at >= today_start
    ])
    
    tasks_completed_this_week = len([
        t for t in tasks 
        if t.status == TaskStatus.COMPLETED and t.completed_at and t.completed_at >= week_start
    ])
    
    tasks_completed_this_month = len([
        t for t in tasks 
        if t.status == TaskStatus.COMPLETED and t.completed_at and t.completed_at >= month_start
    ])
    
    # Calculate average completion time
    completed_with_dates = [
        t for t in tasks 
        if t.status == TaskStatus.COMPLETED and t.created_at and t.completed_at
    ]
    
    if completed_with_dates:
        completion_times = [
            (t.completed_at - t.created_at).total_seconds() / 3600  # hours
            for t in completed_with_dates
        ]
        average_completion_time = sum(completion_times) / len(completion_times)
    else:
        average_completion_time = None
    
    # Simple productivity trend
    last_week_completed = len([
        t for t in tasks 
        if t.status == TaskStatus.COMPLETED and t.completed_at and 
        t.completed_at >= (week_start - timedelta(weeks=1)) and t.completed_at < week_start
    ])
    
    if last_week_completed == 0:
        productivity_trend = "neutral"
    elif tasks_completed_this_week > last_week_completed:
        productivity_trend = "increasing"
    elif tasks_completed_this_week < last_week_completed:
        productivity_trend = "decreasing"
    else:
        productivity_trend = "stable"
    
    return OverviewAnalytics(
        project_analytics=ProjectAnalytics(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            overdue_projects=overdue_projects,
            projects_by_status=projects_by_status,
            projects_by_priority=projects_by_priority
        ),
        task_analytics=TaskAnalytics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            overdue_tasks=overdue_tasks,
            tasks_by_status=tasks_by_status,
            tasks_by_priority=tasks_by_priority,
            completion_rate=completion_rate
        ),
        productivity_metrics=ProductivityMetrics(
            tasks_completed_today=tasks_completed_today,
            tasks_completed_this_week=tasks_completed_this_week,
            tasks_completed_this_month=tasks_completed_this_month,
            average_completion_time=average_completion_time,
            productivity_trend=productivity_trend
        )
    )

@router.get("/project/{project_id}/analytics")
async def get_project_analytics(
    project_id: int,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for a specific project"""
    
    user_id = int(current_user["user_id"])
    
    # Check project access
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
    
    # Get project tasks
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    # Calculate metrics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
    
    # Task distribution by assignee
    assignee_distribution = {}
    for task in tasks:
        if task.assignee_id:
            assignee = db.query(User).filter(User.id == task.assignee_id).first()
            if assignee:
                key = assignee.username
                assignee_distribution[key] = assignee_distribution.get(key, 0) + 1
    
    # Timeline analysis
    timeline_data = []
    if tasks:
        # Group tasks by creation date
        task_dates = {}
        for task in tasks:
            date_key = task.created_at.strftime('%Y-%m-%d')
            task_dates[date_key] = task_dates.get(date_key, 0) + 1
        
        timeline_data = [{"date": k, "count": v} for k, v in sorted(task_dates.items())]
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        "assignee_distribution": assignee_distribution,
        "timeline_data": timeline_data,
        "estimated_vs_actual_hours": {
            "estimated": sum(t.estimated_hours or 0 for t in tasks),
            "actual": sum(t.actual_hours or 0 for t in tasks)
        }
    }

@router.get("/reports/productivity")
async def get_productivity_report(
    days: int = 30,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get productivity report for specified number of days"""
    
    user_id = int(current_user["user_id"])
    
    # Get date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get user's projects
    user_projects = db.query(Project).join(ProjectMember).filter(
        (Project.owner_id == user_id) | (ProjectMember.user_id == user_id)
    ).distinct().all()
    
    project_ids = [p.id for p in user_projects]
    
    if not project_ids:
        return {
            "period": f"Last {days} days",
            "tasks_completed": 0,
            "hours_logged": 0,
            "projects_worked_on": 0,
            "daily_breakdown": []
        }
    
    # Get completed tasks in the period
    completed_tasks = db.query(Task).filter(
        and_(
            Task.project_id.in_(project_ids),
            Task.status == TaskStatus.COMPLETED,
            Task.completed_at >= start_date,
            Task.completed_at <= end_date
        )
    ).all()
    
    # Calculate metrics
    tasks_completed = len(completed_tasks)
    hours_logged = sum(t.actual_hours or 0 for t in completed_tasks)
    projects_worked_on = len(set(t.project_id for t in completed_tasks))
    
    # Daily breakdown
    daily_breakdown = {}
    for task in completed_tasks:
        if task.completed_at:
            date_key = task.completed_at.strftime('%Y-%m-%d')
            if date_key not in daily_breakdown:
                daily_breakdown[date_key] = {"tasks": 0, "hours": 0}
            daily_breakdown[date_key]["tasks"] += 1
            daily_breakdown[date_key]["hours"] += task.actual_hours or 0
    
    # Fill in missing days with zeros
    current_date = start_date
    while current_date <= end_date:
        date_key = current_date.strftime('%Y-%m-%d')
        if date_key not in daily_breakdown:
            daily_breakdown[date_key] = {"tasks": 0, "hours": 0}
        current_date += timedelta(days=1)
    
    daily_data = [
        {
            "date": k,
            "tasks_completed": v["tasks"],
            "hours_logged": v["hours"]
        }
        for k, v in sorted(daily_breakdown.items())
    ]
    
    return {
        "period": f"Last {days} days",
        "tasks_completed": tasks_completed,
        "hours_logged": hours_logged,
        "projects_worked_on": projects_worked_on,
        "daily_breakdown": daily_data
    }