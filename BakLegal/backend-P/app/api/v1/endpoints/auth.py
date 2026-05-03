"""
Authentication API endpoints for login and signup.
"""

import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Response, Cookie
from pydantic import BaseModel, Field, field_validator

from ....db.session import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory session store (for simplicity - in production use Redis/DB)
_sessions: Dict[str, Dict] = {}
SESSION_EXPIRY_HOURS = 24


class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    username: Optional[str] = None


def _hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "baklegal_salt_2024"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def _create_session(user_id: int, username: str) -> str:
    """Create a new session and return session token."""
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "user_id": user_id,
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=SESSION_EXPIRY_HOURS)
    }
    return token


def _validate_session(token: str) -> Optional[Dict]:
    """Validate session token and return session data if valid."""
    if not token or token not in _sessions:
        return None
    session = _sessions[token]
    if datetime.now() > session["expires_at"]:
        del _sessions[token]
        return None
    return session


@router.post("/signup", response_model=AuthResponse)
async def signup(req: SignupRequest, response: Response):
    """Register a new user."""
    db = get_db()
    
    # Check if username already exists
    if db.get_user_by_username(req.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already exists
    if db.get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    password_hash = _hash_password(req.password)
    user_id = db.create_user(req.username, req.email, password_hash)
    
    if user_id is None:
        raise HTTPException(status_code=400, detail="Failed to create user")
    
    # Create session
    token = _create_session(user_id, req.username)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=SESSION_EXPIRY_HOURS * 3600,
        samesite="lax"
    )
    
    return AuthResponse(success=True, message="Account created successfully", username=req.username)


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, response: Response):
    """Login with username and password."""
    db = get_db()
    
    # Get user by username
    user = db.get_user_by_username(req.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Verify password
    password_hash = _hash_password(req.password)
    if user["password"] != password_hash:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create session
    token = _create_session(user["id"], user["username"])
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=SESSION_EXPIRY_HOURS * 3600,
        samesite="lax"
    )
    
    return AuthResponse(success=True, message="Login successful", username=user["username"])


@router.post("/logout", response_model=AuthResponse)
async def logout(response: Response, session_token: str = Cookie(None)):
    """Logout and clear session."""
    if session_token and session_token in _sessions:
        del _sessions[session_token]
    
    response.delete_cookie(key="session_token")
    return AuthResponse(success=True, message="Logged out successfully")


@router.get("/check", response_model=AuthResponse)
async def check_session(session_token: str = Cookie(None)):
    """Check if user is logged in."""
    session = _validate_session(session_token)
    if session:
        return AuthResponse(success=True, message="Authenticated", username=session["username"])
    return AuthResponse(success=False, message="Not authenticated")
