"""
User management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from ..core.database import get_db
from ..core.security import get_current_user_token, get_password_hash
from ..models.user import User

router = APIRouter()

# Pydantic schemas
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    timezone: str
    role: str
    is_active: bool
    avatar_url: Optional[str]
    
    class Config:
        from_attributes = True

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    user = db.query(User).filter(User.id == int(current_user["user_id"])).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    user = db.query(User).filter(User.id == int(current_user["user_id"])).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)