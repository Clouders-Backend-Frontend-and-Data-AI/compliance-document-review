from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.models.base import UserRole
from app.schemas.user import UserCreate, UserLogin, UserOut, Token
from app.api.deps import get_db, get_current_user
from app.core.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Sign up a new user with fixed role: 'advisor' or 'officer'.
    Officer self-signup is disabled unless ALLOW_OFFICER_SIGNUP=true.
    """
    enforce_rate_limit(request, bucket="auth", limit=settings.RATE_LIMIT_AUTH_PER_MINUTE)

    if user_in.role == UserRole.OFFICER and not settings.ALLOW_OFFICER_SIGNUP:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Officer self-registration is disabled. "
                "Set ALLOW_OFFICER_SIGNUP=true for demo, or provision officers via admin seed."
            ),
        )

    if user_in.role not in [UserRole.ADVISOR, UserRole.OFFICER]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be either 'advisor' or 'officer'.",
        )

    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(subject=user.id, role=user.role.value)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/login", response_model=Token)
def login(request: Request, login_data: UserLogin, db: Session = Depends(get_db)):
    """JSON-based login endpoint"""
    enforce_rate_limit(request, bucket="auth", limit=settings.RATE_LIMIT_AUTH_PER_MINUTE)

    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.id, role=user.role.value)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/token", response_model=Token)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 password form login for Swagger Authorize."""
    enforce_rate_limit(request, bucket="auth", limit=settings.RATE_LIMIT_AUTH_PER_MINUTE)

    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.id, role=user.role.value)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Retrieve profile and role of authenticated user"""
    return current_user
