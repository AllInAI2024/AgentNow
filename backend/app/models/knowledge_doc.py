from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Integer, SmallInteger, Boolean, Index, JSON

from app.models import Base


class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="文档ID")
    title = Column(String(500), nullable=False, comment="文档标题")
    file_name = Column(String(500), nullable=False, comment="原始文件名")
    file_path = Column(String(1000), comment="AgentNow 存储路径（相对路径）")
    hermes_path = Column(String(1000), comment="Hermes workspace 中的路径（相对路径）")
    file_size = Column(BigInteger, default=0, comment="文件大小（字节）")
    file_type = Column(String(50), comment="文件类型/扩展名")
    mime_type = Column(String(100), comment="MIME类型")
    content_hash = Column(String(64), comment="文件内容哈希值（SHA256）")
    
    status = Column(SmallInteger, default=1, comment="状态：1-已上传，2-已同步到Hermes，3-处理中，4-失败")
    sync_status = Column(SmallInteger, default=0, comment="同步状态：0-未同步，1-已同步，2-同步失败")
    sync_error = Column(Text, comment="同步失败错误信息")
    synced_at = Column(DateTime, comment="同步到Hermes的时间")
    
    description = Column(Text, comment="文档描述/摘要")
    tags = Column(JSON, comment="标签列表，JSON数组格式")
    category = Column(String(100), comment="文档分类")
    
    created_by = Column(BigInteger, comment="上传者用户ID")
    is_public = Column(Boolean, default=True, comment="是否公开")
    
    embedding_id = Column(String(255), comment="Hermes embedding ID")
    embedding_info = Column(JSON, comment="Hermes embedding 相关信息（JSON格式）")
    
    deleted_at = Column(DateTime, comment="删除时间（软删除）")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_title", "title"),
        Index("idx_file_name", "file_name"),
        Index("idx_status", "status"),
        Index("idx_sync_status", "sync_status"),
        Index("idx_category", "category"),
        Index("idx_created_by", "created_by"),
        Index("idx_created_at", "created_at"),
        Index("idx_deleted_at", "deleted_at"),
    )

    def __repr__(self):
        return f"<KnowledgeDoc(id={self.id}, title={self.title})>"

    def to_dict(self):
        tags = self.tags if isinstance(self.tags, list) else []
        embedding_info = self.embedding_info if isinstance(self.embedding_info, dict) else None
        
        return {
            "id": self.id,
            "title": self.title,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "hermes_path": self.hermes_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "content_hash": self.content_hash,
            "status": self.status,
            "sync_status": self.sync_status,
            "sync_error": self.sync_error,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
            "description": self.description,
            "tags": tags,
            "category": self.category,
            "created_by": self.created_by,
            "is_public": self.is_public,
            "embedding_id": self.embedding_id,
            "embedding_info": embedding_info,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_owner(self, user_id: int) -> bool:
        return self.created_by == user_id
