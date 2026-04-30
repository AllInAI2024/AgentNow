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
from app.models.knowledge_doc import KnowledgeDoc
from app.models.knowledge_config import KnowledgeConfig
from app.models.agent_template import AgentTemplate
from app.models.agent_template_version import AgentTemplateVersion
from app.models.user_agent import UserAgent
from app.models.agent_conversation import AgentConversation
from app.models.agent_generated_file import AgentGeneratedFile
from app.models.agent_operation_log import AgentOperationLog

__all__ = [
    "Base", 
    "engine", 
    "SessionLocal", 
    "User", 
    "Role", 
    "Permission", 
    "Department",
    "UserRole", 
    "RolePermission",
    "KnowledgeDoc",
    "KnowledgeConfig",
    "AgentTemplate",
    "AgentTemplateVersion",
    "UserAgent",
    "AgentConversation",
    "AgentGeneratedFile",
    "AgentOperationLog",
]