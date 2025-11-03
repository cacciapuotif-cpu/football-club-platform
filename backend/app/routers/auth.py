"""Authentication router - login, signup, refresh token."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.database import get_session
from app.dependencies import get_current_user
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.security import create_access_token, create_refresh_token, get_password_hash, verify_password

router = APIRouter()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: str
    organization_slug: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, session: Annotated[AsyncSession, Depends(get_session)]):
    """
    Signup new organization owner.
    Creates organization + owner user.
    """
    # Check if email exists
    result = await session.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Check if org slug exists
    result = await session.execute(select(Organization).where(Organization.slug == request.organization_slug))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization slug already taken")

    # Create organization
    org = Organization(name=request.organization_name, slug=request.organization_slug)
    session.add(org)
    await session.flush()

    # Create owner user
    user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        role=UserRole.OWNER,
        is_active=True,
        is_verified=True,
        organization_id=org.id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, user_id=str(user.id), role=user.role.value
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, session: Annotated[AsyncSession, Depends(get_session)]):
    """Login with email and password."""
    # Find user
    result = await session.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, user_id=str(user.id), role=user.role.value
    )


@router.get("/me")
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user info."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "organization_id": str(current_user.organization_id),
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, session: Annotated[AsyncSession, Depends(get_session)]):
    """Refresh access token using refresh token."""
    from app.security import decode_token

    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Generate new tokens
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token, refresh_token=new_refresh_token, user_id=str(user.id), role=user.role.value
    )
