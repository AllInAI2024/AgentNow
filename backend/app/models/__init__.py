from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.department import Department
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission

__all__ = [
    "Base", 
    "engine", 
    "SessionLocal", 
    "User", 
    "Role", 
    "Permission", 
    "Department",
    "UserRole", 
    "RolePermission"
]