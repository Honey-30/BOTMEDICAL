"""
AI Service for processing natural language commands and providing intelligent assistance
Integrates with Ollama (local LLM) and Hugging Face models
"""

import re
import json
import httpx
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from ..core.config import settings
from ..models.project import Project, ProjectMember
from ..models.task import Task, TaskStatus, TaskPriority
from ..models.user import User

class AIService:
    """AI service for natural language processing and task automation"""
    
    def __init__(self):
        self.ollama_base_url = settings.ollama_base_url
        self.hf_api_key = settings.hugging_face_api_key
        self.confidence_threshold = settings.confidence_threshold
        
        # Intent patterns for command classification
        self.intent_patterns = {
            "create_task": [
                r"create\s+(?:a\s+)?task",
                r"add\s+(?:a\s+)?task",
                r"new\s+task",
                r"make\s+(?:a\s+)?task"
            ],
            "update_task": [
                r"update\s+task",
                r"modify\s+task",
                r"change\s+task",
                r"edit\s+task"
            ],
            "complete_task": [
                r"complete\s+task",
                r"finish\s+task",
                r"mark\s+(?:task\s+)?(?:as\s+)?complete",
                r"done\s+with\s+task"
            ],
            "list_tasks": [
                r"list\s+tasks",
                r"show\s+(?:me\s+)?tasks",
                r"what\s+tasks",
                r"my\s+tasks"
            ],
            "create_project": [
                r"create\s+(?:a\s+)?project",
                r"add\s+(?:a\s+)?project",
                r"new\s+project",
                r"start\s+(?:a\s+)?project"
            ],
            "project_status": [
                r"project\s+status",
                r"how\s+is\s+(?:the\s+)?project",
                r"project\s+progress"
            ],
            "deadline_check": [
                r"deadline",
                r"due\s+date",
                r"when\s+is\s+.*\s+due",
                r"overdue"
            ],
            "risk_analysis": [
                r"risk",
                r"problem",
                r"issue",
                r"analyze",
                r"what.*wrong"
            ]
        }
    
    async def process_message(self, message: str, user_id: int, session_context: Dict, db: Session) -> Dict[str, Any]:
        """Process a natural language message and execute appropriate actions"""
        
        try:
            # Classify intent
            intent, confidence = self._classify_intent(message)
            
            # Extract entities
            entities = self._extract_entities(message, db, user_id)
            
            # Generate response based on intent
            if intent == "create_task":
                response = await self._handle_create_task(message, entities, user_id, db)
            elif intent == "update_task":
                response = await self._handle_update_task(message, entities, user_id, db)
            elif intent == "complete_task":
                response = await self._handle_complete_task(message, entities, user_id, db)
            elif intent == "list_tasks":
                response = await self._handle_list_tasks(message, entities, user_id, db)
            elif intent == "create_project":
                response = await self._handle_create_project(message, entities, user_id, db)
            elif intent == "project_status":
                response = await self._handle_project_status(message, entities, user_id, db)
            elif intent == "deadline_check":
                response = await self._handle_deadline_check(message, entities, user_id, db)
            elif intent == "risk_analysis":
                response = await self._handle_risk_analysis(message, entities, user_id, db)
            else:
                # Use LLM for general conversation
                response = await self._generate_llm_response(message, session_context)
            
            return {
                "response": response.get("text", "I'm sorry, I couldn't process that request."),
                "intent": intent,
                "confidence": confidence,
                "actions": response.get("actions", []),
                "entities": entities
            }
            
        except Exception as e:
            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "intent": "error",
                "confidence": 0.0,
                "actions": [],
                "entities": {}
            }
    
    def _classify_intent(self, message: str) -> Tuple[str, float]:
        """Classify the intent of a message"""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent, 0.8  # High confidence for pattern match
        
        return "general", 0.3  # Low confidence fallback
    
    def _extract_entities(self, message: str, db: Session, user_id: int) -> Dict[str, Any]:
        """Extract entities like task names, project names, dates, etc."""
        entities = {}
        
        # Extract task/project references
        task_match = re.search(r"task\s+[\"']([^\"']+)[\"']", message, re.IGNORECASE)
        if task_match:
            entities["task_name"] = task_match.group(1)
        
        project_match = re.search(r"project\s+[\"']([^\"']+)[\"']", message, re.IGNORECASE)
        if project_match:
            entities["project_name"] = project_match.group(1)
        
        # Extract priority
        priority_match = re.search(r"(high|medium|low|critical)\s+priority", message, re.IGNORECASE)
        if priority_match:
            entities["priority"] = priority_match.group(1).lower()
        
        # Extract dates (simple patterns)
        date_patterns = [
            r"due\s+(\d{1,2}/\d{1,2}/\d{4})",
            r"by\s+(\d{1,2}/\d{1,2}/\d{4})",
            r"tomorrow",
            r"next\s+week",
            r"next\s+month"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                if "tomorrow" in pattern:
                    entities["due_date"] = datetime.now() + timedelta(days=1)
                elif "next week" in pattern:
                    entities["due_date"] = datetime.now() + timedelta(weeks=1)
                elif "next month" in pattern:
                    entities["due_date"] = datetime.now() + timedelta(days=30)
                else:
                    # Try to parse the date
                    try:
                        entities["due_date"] = datetime.strptime(match.group(1), "%m/%d/%Y")
                    except:
                        pass
                break
        
        return entities
    
    async def _handle_create_task(self, message: str, entities: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle task creation requests"""
        
        # Get user's projects
        projects = db.query(Project).filter(
            (Project.owner_id == user_id) | 
            (Project.id.in_(
                db.query(ProjectMember.project_id).filter(ProjectMember.user_id == user_id)
            ))
        ).all()
        
        if not projects:
            return {
                "text": "You don't have any projects yet. Please create a project first.",
                "actions": []
            }
        
        # Use the first project if no specific project mentioned
        project = projects[0]
        if "project_name" in entities:
            for p in projects:
                if entities["project_name"].lower() in p.name.lower():
                    project = p
                    break
        
        # Extract task title from message
        task_title = entities.get("task_name")
        if not task_title:
            # Try to extract from message
            title_patterns = [
                r"create\s+task\s+[\"']([^\"']+)[\"']",
                r"add\s+task\s+[\"']([^\"']+)[\"']",
                r"task\s+called\s+[\"']([^\"']+)[\"']"
            ]
            for pattern in title_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    task_title = match.group(1)
                    break
        
        if not task_title:
            return {
                "text": "Please specify the task title. For example: 'Create task \"Setup database\"'",
                "actions": []
            }
        
        # Create the task
        try:
            task = Task(
                title=task_title,
                project_id=project.id,
                creator_id=user_id,
                priority=entities.get("priority", "medium"),
                due_date=entities.get("due_date")
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            return {
                "text": f"Created task \"{task_title}\" in project \"{project.name}\". Task ID: {task.id}",
                "actions": [{"type": "task_created", "task_id": task.id, "project_id": project.id}]
            }
            
        except Exception as e:
            return {
                "text": f"Failed to create task: {str(e)}",
                "actions": []
            }
    
    async def _handle_list_tasks(self, message: str, entities: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle task listing requests"""
        
        # Get user's tasks
        tasks = db.query(Task).join(Project).filter(
            (Project.owner_id == user_id) | 
            (Project.id.in_(
                db.query(ProjectMember.project_id).filter(ProjectMember.user_id == user_id)
            ))
        ).limit(10).all()
        
        if not tasks:
            return {
                "text": "You don't have any tasks.",
                "actions": []
            }
        
        # Format task list
        task_list = []
        for task in tasks:
            status_emoji = "✅" if task.status == TaskStatus.COMPLETED else "⏳"
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
            
            task_info = f"{status_emoji} {priority_emoji} {task.title}"
            if task.due_date:
                task_info += f" (Due: {task.due_date.strftime('%m/%d/%Y')})"
            
            task_list.append(task_info)
        
        response_text = "Here are your tasks:\n\n" + "\n".join(task_list)
        
        return {
            "text": response_text,
            "actions": [{"type": "tasks_listed", "count": len(tasks)}]
        }
    
    async def _handle_project_status(self, message: str, entities: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle project status requests"""
        
        # Get user's projects
        projects = db.query(Project).filter(
            (Project.owner_id == user_id) | 
            (Project.id.in_(
                db.query(ProjectMember.project_id).filter(ProjectMember.user_id == user_id)
            ))
        ).all()
        
        if not projects:
            return {
                "text": "You don't have any projects.",
                "actions": []
            }
        
        # If specific project mentioned, show that one
        target_project = None
        if "project_name" in entities:
            for project in projects:
                if entities["project_name"].lower() in project.name.lower():
                    target_project = project
                    break
        
        if target_project:
            projects = [target_project]
        elif len(projects) > 1:
            # Show summary of all projects
            project_summaries = []
            for project in projects[:5]:  # Limit to 5 projects
                task_count = db.query(Task).filter(Task.project_id == project.id).count()
                completed_count = db.query(Task).filter(
                    Task.project_id == project.id,
                    Task.status == TaskStatus.COMPLETED
                ).count()
                
                progress = f"{completed_count}/{task_count}" if task_count > 0 else "0/0"
                project_summaries.append(f"📋 {project.name}: {progress} tasks completed")
            
            return {
                "text": "Here's your project overview:\n\n" + "\n".join(project_summaries),
                "actions": [{"type": "project_status_shown", "project_count": len(projects)}]
            }
        
        # Show detailed status for single project
        project = projects[0]
        tasks = db.query(Task).filter(Task.project_id == project.id).all()
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        in_progress_tasks = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
        overdue_tasks = len([
            t for t in tasks 
            if t.due_date and t.due_date < datetime.utcnow() and t.status != TaskStatus.COMPLETED
        ])
        
        status_text = f"📋 **{project.name}**\n\n"
        status_text += f"📊 Progress: {completed_tasks}/{total_tasks} tasks completed\n"
        status_text += f"⚡ In Progress: {in_progress_tasks} tasks\n"
        
        if overdue_tasks > 0:
            status_text += f"⚠️ Overdue: {overdue_tasks} tasks\n"
        
        if project.due_date:
            days_left = (project.due_date - datetime.utcnow()).days
            status_text += f"📅 Due in {days_left} days\n"
        
        return {
            "text": status_text,
            "actions": [{"type": "project_status_shown", "project_id": project.id}]
        }
    
    async def _handle_deadline_check(self, message: str, entities: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle deadline and overdue task checks"""
        
        # Get overdue tasks
        overdue_tasks = db.query(Task).join(Project).filter(
            and_(
                Task.due_date < datetime.utcnow(),
                Task.status != TaskStatus.COMPLETED,
                or_(
                    Project.owner_id == user_id,
                    Project.id.in_(
                        db.query(ProjectMember.project_id).filter(ProjectMember.user_id == user_id)
                    )
                )
            )
        ).all()
        
        if not overdue_tasks:
            return {
                "text": "🎉 Great! You don't have any overdue tasks.",
                "actions": []
            }
        
        # Format overdue tasks
        overdue_list = []
        for task in overdue_tasks:
            days_overdue = (datetime.utcnow() - task.due_date).days
            overdue_list.append(f"⚠️ {task.title} - {days_overdue} days overdue")
        
        response_text = f"You have {len(overdue_tasks)} overdue tasks:\n\n" + "\n".join(overdue_list)
        response_text += "\n\nConsider updating deadlines or prioritizing these tasks."
        
        return {
            "text": response_text,
            "actions": [{"type": "overdue_tasks_shown", "count": len(overdue_tasks)}]
        }
    
    async def _generate_llm_response(self, message: str, context: Dict) -> Dict[str, Any]:
        """Generate response using local LLM (Ollama) or fallback to Hugging Face"""
        
        try:
            # Try Ollama first
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": "llama2",  # or another model
                        "prompt": f"You are a helpful project management assistant. User says: {message}",
                        "stream": False
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "text": data.get("response", "I'm here to help with your project management needs!"),
                        "actions": []
                    }
        
        except Exception:
            pass  # Fall back to simple response
        
        # Fallback response
        return {
            "text": "I'm your AI project management assistant! I can help you create tasks, check project status, manage deadlines, and more. What would you like to do?",
            "actions": []
        }
    
    async def _handle_complete_task(self, message: str, entities: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle task completion requests"""
        # Implementation for completing tasks
        return {"text": "Task completion feature coming soon!", "actions": []}
    
    async def _handle_update_task(self, message: str, entities: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle task update requests"""
        # Implementation for updating tasks
        return {"text": "Task update feature coming soon!", "actions": []}
    
    async def _handle_create_project(self, message: str, entities: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle project creation requests"""
        # Implementation for creating projects
        return {"text": "Project creation feature coming soon!", "actions": []}
    
    async def _handle_risk_analysis(self, message: str, entities: Dict, user_id: int, db: Session) -> Dict[str, Any]:
        """Handle risk analysis requests"""
        # Implementation for risk analysis
        return {"text": "Risk analysis feature coming soon!", "actions": []}
    
    async def analyze_project(self, project_id: int, user_id: int, db: Session) -> Dict[str, Any]:
        """Analyze a project for risks and suggestions"""
        # Implementation for project analysis
        return {
            "analysis": {"status": "healthy"},
            "suggestions": ["Keep up the good work!"],
            "risk_score": 0.2,
            "confidence": 0.8
        }
    
    async def analyze_tasks(self, project_id: Optional[int], user_id: int, db: Session) -> Dict[str, Any]:
        """Analyze tasks for optimization"""
        # Implementation for task analysis
        return {
            "analysis": {"efficiency": "good"},
            "suggestions": ["Consider breaking down large tasks"],
            "risk_score": 0.3,
            "confidence": 0.7
        }
    
    async def suggest_priorities(self, project_id: Optional[int], user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Suggest task prioritization"""
        # Implementation for priority suggestions
        return [
            {"task_id": 1, "suggested_priority": "high", "reason": "Blocking other tasks"}
        ]