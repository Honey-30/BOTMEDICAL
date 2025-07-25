"""
Authentication API endpoints
Adapted from existing Flask auth with FastAPI patterns
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import httpx

from ..core.database import get_db
from ..core.security import (
    create_access_token, create_refresh_token, get_password_hash, 
    verify_password, get_current_user_token
)
from ..models.user import User, UserRole

router = APIRouter()
security = HTTPBearer()

# Pydantic schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

class GitHubOAuthRequest(BaseModel):
    code: str
    redirect_uri: str

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=UserRole.USER
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(db_user.id), "roles": [db_user.role]})
    refresh_token = create_refresh_token(data={"sub": str(db_user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(db_user)
    }

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return tokens"""
    
    # Find user
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id), "roles": [user.role]})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@router.post("/github-oauth", response_model=Token)
async def github_oauth(oauth_request: GitHubOAuthRequest, db: Session = Depends(get_db)):
    """Authenticate with GitHub OAuth"""
    
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        # Get access token from GitHub
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": "your-github-client-id",  # From config
                "client_secret": "your-github-client-secret",  # From config
                "code": oauth_request.code,
                "redirect_uri": oauth_request.redirect_uri
            },
            headers={"Accept": "application/json"}
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange GitHub code for token"
            )
        
        token_data = token_response.json()
        github_token = token_data.get("access_token")
        
        # Get user info from GitHub
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from GitHub"
            )
        
        github_user = user_response.json()
    
    # Find or create user
    user = db.query(User).filter(User.github_id == str(github_user["id"])).first()
    
    if not user:
        # Create new user from GitHub data
        user = User(
            username=github_user["login"],
            email=github_user.get("email", f"{github_user['login']}@github.local"),
            full_name=github_user.get("name"),
            github_id=str(github_user["id"]),
            github_username=github_user["login"],
            avatar_url=github_user.get("avatar_url"),
            bio=github_user.get("bio"),
            location=github_user.get("location"),
            is_verified=True,
            hashed_password="github_oauth",  # Placeholder
            role=UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id), "roles": [user.role]})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    user = db.query(User).filter(User.id == int(current_user["user_id"])).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user_token)):
    """Logout user (invalidate token on client side)"""
    return {"message": "Successfully logged out"}