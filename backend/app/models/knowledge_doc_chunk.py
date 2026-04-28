from datetime import datetime
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Integer, Index, JSON, ForeignKey

from app.models import Base


class KnowledgeDocChunk(Base):
    __tablename__ = "knowledge_doc_chunks"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="分块ID")
    doc_id = Column(BigInteger, ForeignKey("knowledge_docs.id", ondelete="CASCADE"), nullable=False, comment="所属文档ID")
    
    chunk_index = Column(Integer, comment="分块序号")
    chunk_content = Column(Text, comment="分块原文内容")
    chunk_hash = Column(String(64), comment="分块内容哈希")
    
    start_position = Column(BigInteger, comment="起始位置")
    end_position = Column(BigInteger, comment="结束位置")
    char_count = Column(Integer, comment="字符数")
    token_count = Column(Integer, comment="预估token数")
    
    hermes_embedding_id = Column(String(255), comment="Hermes embedding ID")
    embedding_info = Column(JSON, comment="Embedding 元信息")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        Index("idx_doc_id", "doc_id"),
        Index("idx_chunk_index", "chunk_index"),
        Index("idx_hermes_embedding_id", "hermes_embedding_id"),
    )

    def __repr__(self):
        return f"<KnowledgeDocChunk(id={self.id}, doc_id={self.doc_id}, chunk_index={self.chunk_index})>"

    def to_dict(self):
        embedding_info = self.embedding_info if isinstance(self.embedding_info, dict) else None
        
        return {
            "id": self.id,
            "doc_id": self.doc_id,
            "chunk_index": self.chunk_index,
            "chunk_content": self.chunk_content,
            "chunk_hash": self.chunk_hash,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "char_count": self.char_count,
            "token_count": self.token_count,
            "hermes_embedding_id": self.hermes_embedding_id,
            "embedding_info": embedding_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
