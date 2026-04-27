from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models import SessionLocal, User

security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
    }
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except JWTError:
        return None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    user_id = decode_access_token(token)
    
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return current_user


def init_default_admin(db: Session) -> None:
    admin = db.query(User).filter(User.phone == settings.DEFAULT_ADMIN_PHONE).first()
    
    if admin is None:
        old_admin = db.query(User).filter(User.role == "admin").first()
        
        if old_admin is not None:
            old_admin.phone = settings.DEFAULT_ADMIN_PHONE
            old_admin.password_hash = get_password_hash(settings.DEFAULT_ADMIN_PASSWORD)
            old_admin.username = settings.DEFAULT_ADMIN_USERNAME
            old_admin.is_active = True
            old_admin.is_default_password = True
            db.commit()
        else:
            default_admin = User(
                phone=settings.DEFAULT_ADMIN_PHONE,
                password_hash=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                username=settings.DEFAULT_ADMIN_USERNAME,
                role="admin",
                is_active=True,
                is_default_password=True,
            )
            db.add(default_admin)
            db.commit()
            db.refresh(default_admin)
    else:
        if not verify_password(settings.DEFAULT_ADMIN_PASSWORD, admin.password_hash):
            admin.password_hash = get_password_hash(settings.DEFAULT_ADMIN_PASSWORD)
            admin.is_default_password = True
            db.commit()
