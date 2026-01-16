"""
Authentication API Endpoints
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
import logging

from app.db.users import user_repository
from app.core.jwt_utils import create_access_token, get_user_from_token

logger = logging.getLogger(__name__)

router = APIRouter()


# =========================================
# Request/Response Models
# =========================================

class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User email")
    name: str = Field(..., min_length=2, max_length=100, description="User name")
    password: str = Field(..., min_length=6, max_length=100, description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "أحمد محمد",
                "password": "password123"
            }
        }


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }


class AuthResponse(BaseModel):
    """Authentication response"""
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[dict] = None


class UserResponse(BaseModel):
    """User info response"""
    id: str
    email: str
    name: str


# =========================================
# Dependencies
# =========================================

async def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract and validate user from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user


# =========================================
# Endpoints
# =========================================

@router.post(
    "/auth/register",
    response_model=AuthResponse,
    summary="Register new user",
    description="Create a new user account"
)
async def register(request: RegisterRequest):
    """Register a new user"""
    logger.info(f"Registration attempt for: {request.email}")
    
    user = await user_repository.create_user(
        email=request.email,
        name=request.name,
        password=request.password
    )
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="البريد الإلكتروني مستخدم بالفعل"
        )
    
    # Create token
    token = create_access_token(user["id"], user["email"], user["name"])
    
    return AuthResponse(
        success=True,
        message="تم إنشاء الحساب بنجاح",
        token=token,
        user=user
    )


@router.post(
    "/auth/login",
    response_model=AuthResponse,
    summary="User login",
    description="Authenticate user and get access token"
)
async def login(request: LoginRequest):
    """Login user"""
    logger.info(f"Login attempt for: {request.email}")
    
    user = await user_repository.authenticate(
        email=request.email,
        password=request.password
    )
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="بيانات الدخول غير صحيحة"
        )
    
    # Create token
    token = create_access_token(user["id"], user["email"], user["name"])
    
    return AuthResponse(
        success=True,
        message="تم تسجيل الدخول بنجاح",
        token=token,
        user=user
    )


@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get authenticated user info"
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    user = await user_repository.get_user_by_id(current_user["user_id"])
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**user)


@router.post(
    "/auth/logout",
    summary="Logout user",
    description="Logout current user (client should discard token)"
)
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user - client should discard token"""
    return {
        "success": True,
        "message": "تم تسجيل الخروج بنجاح"
    }
