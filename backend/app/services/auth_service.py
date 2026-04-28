from datetime import datetime, timedelta
from typing import Optional, List

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.config import settings
from app.models import SessionLocal, User, Role, Permission, UserRole, RolePermission

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


def get_user_roles(db: Session, user_id: int) -> List[Role]:
    roles = db.query(Role).join(
        UserRole, UserRole.role_id == Role.id
    ).filter(
        UserRole.user_id == user_id
    ).all()
    return roles


def get_user_permissions(db: Session, user_id: int) -> List[Permission]:
    user = db.query(User).filter(User.id == user_id).first()
    
    if user and user.is_super_admin:
        return db.query(Permission).order_by(Permission.parent_id).all()
    
    permissions = db.query(Permission).distinct().join(
        RolePermission, RolePermission.permission_id == Permission.id
    ).join(
        Role, Role.id == RolePermission.role_id
    ).join(
        UserRole, UserRole.role_id == Role.id
    ).filter(
        UserRole.user_id == user_id
    ).order_by(Permission.parent_id).all()
    return permissions


def get_user_menu_permissions(db: Session, user_id: int) -> List[Permission]:
    user = db.query(User).filter(User.id == user_id).first()
    
    if user and user.is_super_admin:
        return db.query(Permission).filter(
            Permission.type.in_([1, 2])
        ).order_by(Permission.parent_id).all()
    
    all_permissions = db.query(Permission).distinct().join(
        RolePermission, RolePermission.permission_id == Permission.id
    ).join(
        Role, Role.id == RolePermission.role_id
    ).join(
        UserRole, UserRole.role_id == Role.id
    ).filter(
        UserRole.user_id == user_id
    ).all()
    
    if not all_permissions:
        return []
    
    menu_ids = set()
    permission_map = {}
    
    all_db_permissions = db.query(Permission).all()
    for p in all_db_permissions:
        permission_map[p.id] = p
    
    for perm in all_permissions:
        current_id = perm.id
        while current_id > 0:
            current_perm = permission_map.get(current_id)
            if current_perm and current_perm.type in [1, 2]:
                menu_ids.add(current_id)
            if current_perm:
                current_id = current_perm.parent_id
            else:
                break
    
    if not menu_ids:
        return []
    
    return db.query(Permission).filter(
        Permission.id.in_(menu_ids)
    ).order_by(Permission.parent_id).all()


def get_user_all_permission_codes(db: Session, user_id: int) -> List[str]:
    user = db.query(User).filter(User.id == user_id).first()
    
    if user and user.is_super_admin:
        permissions = db.query(Permission.code).all()
        return [p[0] for p in permissions]
    
    permissions = db.query(Permission.code).distinct().join(
        RolePermission, RolePermission.permission_id == Permission.id
    ).join(
        Role, Role.id == RolePermission.role_id
    ).join(
        UserRole, UserRole.role_id == Role.id
    ).filter(
        UserRole.user_id == user_id
    ).all()
    return [p[0] for p in permissions]


def check_user_permission(db: Session, user_id: int, permission_code: str) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    
    if user and user.is_super_admin:
        return True
    
    exists = db.query(Permission).join(
        RolePermission, RolePermission.permission_id == Permission.id
    ).join(
        Role, Role.id == RolePermission.role_id
    ).join(
        UserRole, UserRole.role_id == Role.id
    ).filter(
        UserRole.user_id == user_id,
        Permission.code == permission_code
    ).first() is not None
    
    return exists


def require_permission(db: Session, user_id: int, permission_code: str):
    if not check_user_permission(db, user_id, permission_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"没有权限: {permission_code}"
        )


class PermissionChecker:
    def __init__(self, permission_code: str):
        self.permission_code = permission_code

    def __call__(
        self,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> User:
        require_permission(db, current_user.id, self.permission_code)
        return current_user


def permission_required(permission_code: str):
    return PermissionChecker(permission_code)


def get_super_admin_role(db: Session) -> Optional[Role]:
    role = db.query(Role).filter(
        Role.code == "super_admin"
    ).first()
    return role


def assign_role_to_user(db: Session, user_id: int, role_id: int, created_by: Optional[int] = None):
    existing = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id
    ).first()
    
    if existing is None:
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id
        )
        db.add(user_role)
        db.commit()


def init_default_admin(db: Session) -> None:
    admin = db.query(User).filter(User.phone == settings.DEFAULT_ADMIN_PHONE).first()
    
    super_admin_role = get_super_admin_role(db)
    
    if admin is None:
        default_admin = User(
            phone=settings.DEFAULT_ADMIN_PHONE,
            email=None,
            password_hash=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
            username=settings.DEFAULT_ADMIN_USERNAME,
            is_super_admin=True,
            is_active=True,
            is_default_password=True,
        )
        db.add(default_admin)
        db.commit()
        db.refresh(default_admin)
        
        if super_admin_role:
            assign_role_to_user(db, default_admin.id, super_admin_role.id)
    else:
        if not verify_password(settings.DEFAULT_ADMIN_PASSWORD, admin.password_hash):
            admin.password_hash = get_password_hash(settings.DEFAULT_ADMIN_PASSWORD)
            admin.is_default_password = True
            db.commit()
        
        if super_admin_role:
            assign_role_to_user(db, admin.id, super_admin_role.id)