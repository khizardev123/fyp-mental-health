import re

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.core.config import settings
from app.database.models import User
from app.database.session import get_db

router = APIRouter()

_OBJECT_ID_RE = re.compile(r"^[a-fA-F0-9]{24}$")


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


class MeResponse(BaseModel):
    user: dict


class ProvisionRequest(BaseModel):
    """Upsert a SQLite user using the MongoDB ObjectId as the primary key."""

    id: str = Field(..., min_length=24, max_length=36)
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr


class ProvisionResponse(BaseModel):
    created: bool
    user: dict


def require_internal_provision(
    request: Request,
    x_internal_provision_secret: str | None = Header(default=None),
) -> None:
    """
    Protect /auth/provision for internal callers only.

    - If INTERNAL_PROVISION_SECRET is set: require matching X-Internal-Provision-Secret.
    - If unset: allow only localhost (Phase 2 local development fallback).
    """
    secret = (settings.INTERNAL_PROVISION_SECRET or "").strip()
    client_host = request.client.host if request.client else ""
    is_local = client_host in {"127.0.0.1", "::1", "localhost"}

    if secret:
        if not x_internal_provision_secret or x_internal_provision_secret != secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing internal provision secret",
            )
        return

    if not is_local:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provision endpoint requires INTERNAL_PROVISION_SECRET when not called from localhost",
        )


@router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        name=request.name.strip(),
        email=request.email.lower(),
        password_hash=hash_password(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email, name=user.name)
    return {
        "token": token,
        "user": {"id": user.id, "name": user.name, "email": user.email},
    }


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user or not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user_id=user.id, email=user.email, name=user.name)
    return {
        "token": token,
        "user": {"id": user.id, "name": user.name, "email": user.email},
    }


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
        }
    }


@router.post("/provision", response_model=ProvisionResponse)
def provision_user(
    request: ProvisionRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_provision),
):
    """
    Internal upsert used by Next.js after MongoDB register/login.

    Stores users.id = MongoDB ObjectId string (no UUID generation when id is supplied).
    password_hash remains NULL — passwords stay in MongoDB only.
    """
    user_id = request.id.strip()
    if not _OBJECT_ID_RE.fullmatch(user_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="id must be a 24-character MongoDB ObjectId hex string",
        )

    name = request.name.strip()
    email = request.email.lower().strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="name is required",
        )

    # Email must not belong to a different user id.
    email_owner = db.query(User).filter(User.email == email).first()
    if email_owner and email_owner.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered to a different user",
        )

    existing = db.get(User, user_id)
    if existing:
        existing.name = name
        existing.email = email
        # Keep password_hash as-is (typically NULL for provisioned users).
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return {
            "created": False,
            "user": {
                "id": existing.id,
                "name": existing.name,
                "email": existing.email,
            },
        }

    user = User(
        id=user_id,
        name=name,
        email=email,
        password_hash=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "created": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
    }
