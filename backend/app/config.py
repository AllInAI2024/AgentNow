import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "智现 AgentNow 企业智能体平台"
    PROJECT_VERSION: str = "0.2.0"
    API_PREFIX: str = "/api/v1"
    
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 5116
    
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/agentnow"
    
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    DEFAULT_ADMIN_PHONE: str = "13651165117"
    DEFAULT_ADMIN_PASSWORD: str = "123456"
    DEFAULT_ADMIN_USERNAME: str = "系统管理员"
    
    HERMES_BASE_URL: Optional[str] = None
    
    KNOWLEDGE_BASE_PATH: str = os.path.expanduser("~/.agentnow/knowledge/docs")
    KNOWLEDGE_MAX_FILE_SIZE: int = 100 * 1024 * 1024
    KNOWLEDGE_ALLOWED_TYPES: str = ".pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls,.pptx,.ppt,.html,.htm,.xml"
    
    GENERATED_FILES_PATH: str = os.path.expanduser("~/.agentnow/generated")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
