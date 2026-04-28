from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Boolean, Index, JSON
import re

from app.models import Base


class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="文档ID")
    title = Column(String(500), nullable=False, comment="文档标题")
    file_name = Column(String(500), nullable=False, comment="文件名")
    file_path = Column(String(1000), nullable=False, comment="相对存储路径（相对于知识库根目录）")
    
    file_size = Column(BigInteger, default=0, comment="文件大小（字节）")
    file_type = Column(String(50), comment="文件类型/扩展名")
    mime_type = Column(String(100), comment="MIME类型")
    content_hash = Column(String(64), comment="文件内容哈希值（SHA256）")
    
    description = Column(Text, comment="文档描述/摘要")
    tags = Column(JSON, comment="标签列表，JSON数组格式")
    category = Column(String(100), comment="文档分类")
    
    created_by = Column(BigInteger, comment="创建者用户ID")
    updated_by = Column(BigInteger, comment="最后更新者用户ID")
    is_public = Column(Boolean, default=True, comment="是否公开")
    
    word_count = Column(BigInteger, default=0, comment="字数统计（仅文本文件）")
    file_modified_at = Column(DateTime, comment="文件最后修改时间")
    
    deleted_at = Column(DateTime, comment="删除时间（软删除）")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_title", "title"),
        Index("idx_file_name", "file_name"),
        Index("idx_category", "category"),
        Index("idx_created_by", "created_by"),
        Index("idx_created_at", "created_at"),
        Index("idx_deleted_at", "deleted_at"),
    )

    def __repr__(self):
        return f"<KnowledgeDoc(id={self.id}, title={self.title})>"

    def to_dict(self):
        tags = self.tags if isinstance(self.tags, list) else []
        
        return {
            "id": self.id,
            "title": self.title,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "content_hash": self.content_hash,
            "description": self.description,
            "tags": tags,
            "category": self.category,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "is_public": self.is_public,
            "word_count": self.word_count,
            "file_modified_at": self.file_modified_at.isoformat() if self.file_modified_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_owner(self, user_id: int) -> bool:
        return self.created_by == user_id

    def is_editable(self, user: dict) -> bool:
        if user.get("is_super_admin"):
            return True
        return self.created_by == user.get("id")

    def is_deletable(self, user: dict) -> bool:
        if user.get("is_super_admin"):
            return True
        return self.created_by == user.get("id")

    def get_safe_filename(self, filename: str) -> str:
        safe = re.sub(r'[\\/:*?"<>|]', '_', filename)
        return safe.strip()

    def is_markdown(self) -> bool:
        ext = (self.file_type or "").lower().lstrip('.')
        return ext == 'md'

    def is_text_file(self) -> bool:
        ext = (self.file_type or "").lower().lstrip('.')
        text_exts = {'txt', 'md', 'json', 'csv', 'xml', 'html', 'htm'}
        return ext in text_exts
