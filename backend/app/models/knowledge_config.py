from datetime import datetime
from typing import Optional
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Index

from app.models import Base


class KnowledgeConfig(Base):
    __tablename__ = "knowledge_configs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="配置ID")
    config_key = Column(String(100), nullable=False, unique=True, comment="配置键")
    config_value = Column(Text, comment="配置值")
    description = Column(String(500), comment="配置描述")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_config_key", "config_key"),
    )

    def __repr__(self):
        return f"<KnowledgeConfig(id={self.id}, config_key={self.config_key})>"

    def to_dict(self):
        return {
            "id": self.id,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def get_config_keys():
        return {
            "storage.base_path": "./data/knowledge_docs",
            "hermes.workspace_path": "~/.hermes/workspace/docs",
            "sync.auto_sync": "true",
            "file.max_size": "104857600",
            "file.allowed_types": ".pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls,.pptx,.ppt,.html,.htm,.xml",
            "embedding.enabled": "false",
        }
